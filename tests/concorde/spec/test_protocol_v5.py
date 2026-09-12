"""Protocol 5 context, ownership, byte identity and authority regressions."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.development.capability_host import CapabilityHost, _target_revision
from concorde.development.capability_service import run_capability
from concorde.harness.context import (resolve_context, recheck_context,
    resolve_discovery_context, recheck_discovery_context)
from concorde.spec.repository import SpecRepository, SpecError, digest
from concorde.spec.typed_data import typed, validate_typed, TypedDataError
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.spec.support import project, PACKAGE, CONFIGURATION, ModelProcessDouble, block


class ProtocolFiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = project(self.root)

    def save(self):
        (self.root / '.concorde/specs.json').write_text(json.dumps(self.registry))

    def repository(self):
        return SpecRepository(self.root, PACKAGE)

    def reference(self, consumer, kind, identity):
        next(t for t in self.registry['targets'] if t['id'] == consumer)['references'].append(
            {'kind': kind, 'id': identity})
        self.save()

    @verifies('scenario.spec.reference-resolution')
    def test_overlap_cycles_and_scenario_query_keep_unique_owner_and_stop_after_one_level(self):
        self.reference('scope.bank', 'module', 'service.transfer')
        self.reference('scope.bank', 'document', 'document.transfer.promises')
        self.reference('service.transfer', 'module', 'module.ledger')
        self.reference('module.ledger', 'module', 'scope.bank')
        r = self.repository()
        resolved = r.spec_context('scope.bank').value
        paths = [source['path'] for source in resolved['sources']]
        self.assertEqual(sorted(set(paths)), paths)
        self.assertNotIn('specs/ledger/module.md', paths)
        promise = next(s for s in resolved['sources'] if s['document_id'] == 'document.transfer.promises')
        self.assertEqual('service.transfer', promise['owner'])
        self.assertEqual([{'kind': 'document', 'id': 'document.transfer.promises'},
                          {'kind': 'module', 'id': 'service.transfer'}], promise['reasons'])
        scenario = r.spec_context('scenario.transfer.debit').value
        self.assertEqual('service.transfer', scenario['module_id'])
        self.assertIn('specs/ledger/module.md', [s['path'] for s in scenario['sources']])
        self.assertEqual(r.spec_files('service.transfer'), r.spec_files('scenario.transfer.debit'))
        self.assertEqual(('scope.bank', 'service.transfer'), r.context_users('document.transfer.promises'))
        self.assertEqual(['scenario.bank.settlement'], [s.id for s in r.scenarios(r.select('scope.bank'))])

    def test_locator_does_not_load_document_bodies(self):
        self.reference('scope.bank', 'document', 'document.transfer.promises')
        r = self.repository()
        with patch.object(r, 'document', side_effect=AssertionError('body read')):
            self.assertEqual(('specs/bank/module.md', 'specs/transfer/promises.md'), r.spec_files('scope.bank'))

    def test_reference_changes_with_identical_files_invalidate_snapshot_discovery_and_revision(self):
        self.reference('scope.bank', 'module', 'service.transfer')
        old = self.repository()
        snap = resolve_context(old, 'scope.bank')
        discovery = resolve_discovery_context(old, ('scope.bank',), capability='concorde-main', phase='route', task='Read')
        revision = _target_revision(old, old.select('scope.bank'))
        self.reference('scope.bank', 'document', 'document.transfer.promises')
        new = self.repository()
        self.assertEqual(old.spec_files('scope.bank'), new.spec_files('scope.bank'))
        self.assertNotEqual(revision, _target_revision(new, new.select('scope.bank')))
        for check, snapshot in ((recheck_context, snap), (recheck_discovery_context, discovery)):
            with self.assertRaisesRegex(SpecError, 'changed'):
                check(new, snapshot)

    def test_source_bytes_are_exact_and_discovery_injects_each_body_once(self):
        path = self.root / 'specs/transfer/promises.md'
        raw = path.read_bytes().replace(b'\n', b'\r\n')
        path.write_bytes(raw)
        self.reference('module.ledger', 'document', 'document.transfer.promises')
        r = self.repository()
        source = next(s for s in r.spec_context('module.ledger').sources if s['path'].endswith('promises.md'))
        self.assertEqual(digest(raw), source['digest'])
        self.assertEqual(raw, source['content'].encode())
        snap = resolve_discovery_context(r, ('service.transfer', 'module.ledger'), capability='concorde-main', phase='route', task='Read').value
        self.assertEqual(1, sum(s['path'].endswith('promises.md') for s in snap['documents']))
        self.assertTrue(all('content' not in s for t in snap['targets'] for s in t['spec_resolution']['sources']))
        self.assertTrue(all('reasons' not in s for s in snap['documents']))

    @verifies('scenario.spec.reference-invalid')
    def test_invalid_reference_kinds_unknown_self_and_duplicates_fail_closed(self):
        for refs in ([{'kind': 'path', 'id': 'document.transfer.promises'}],
                     [{'kind': 'module', 'id': 'document.transfer.promises'}],
                     [{'kind': 'document', 'id': 'service.transfer'}],
                     [{'kind': 'module', 'id': 'scope.bank'}],
                     [{'kind': 'document', 'id': 'document.bank'}],
                     [{'kind': 'module', 'id': 'service.transfer'}] * 2):
            with self.subTest(refs=refs):
                self.registry['targets'][0]['references'] = refs
                self.save()
                with self.assertRaises(SpecError):
                    self.repository().spec_context('scope.bank')

    def test_missing_bytes_bad_utf8_and_owner_mismatch_never_return_partial_context(self):
        self.reference('scope.bank', 'document', 'document.transfer.promises')
        path = self.root / 'specs/transfer/promises.md'
        raw = path.read_bytes()
        for replacement in (None, raw + b'\xff', raw.replace(b'service.transfer', b'module.ledger')):
            with self.subTest(replacement=replacement):
                if replacement is None:
                    path.unlink()
                else:
                    path.write_bytes(replacement)
                with self.assertRaises((SpecError, UnicodeError)):
                    self.repository().spec_context('scope.bank')
                path.write_bytes(raw)

    def test_foreign_documents_never_add_definitions_files_or_write_authority(self):
        self.reference('service.transfer', 'module', 'module.ledger')
        r = self.repository()
        target = r.select('service.transfer')
        self.assertNotIn('app/ledger.py', r.implementation_files(target))
        self.assertTrue(all(e.owner == target.id for e in r.entities(target)))
        snap = resolve_context(r, target.id, phase='implementation').value
        self.assertNotIn('app/ledger.py', [a['path'] for a in snap['implementation_artifacts']])
        before = (self.root / 'specs/ledger/module.md').read_bytes()
        def callback(stage, snapshot, result, cwd):
            if stage == 'specify':
                result['documents'] = [{'path': 'specs/ledger/module.md', 'content': before.decode() + '\nUnauthorized.\n'}]
        double = ModelProcessDouble(callback)
        host = CapabilityHost(self.root, PACKAGE, executor=double.executor, allow_primary_worktree=True)
        result = run_capability('concorde-specify', CONFIGURATION,
            typed('concorde-specify-request', {'target_id': target.id, 'task': 'Clarify'}), host_context=host)
        self.assertEqual('blocked', result['status'])
        self.assertEqual(before, (self.root / 'specs/ledger/module.md').read_bytes())

    def test_canonical_contract_and_complementary_bindings_are_independent(self):
        self.reference('service.transfer', 'document', 'document.ledger.api')
        definition = {'id': 'contract.ledger.read', 'version': 2, 'schema': {'type': 'integer'},
                      'semantics': 'Return the stored balance.', 'example': 42}
        for owner, peer, role, path in [('module.ledger', 'service.transfer', 'provided', 'specs/ledger/module.md'),
                                      ('service.transfer', 'module.ledger', 'required', 'specs/transfer/module.md')]:
            binding = {'id': definition['id'], 'version': 2, 'role': role, 'peer': peer,
                       'selection_condition': 'When reading a balance.',
                       'relied_upon_guarantees': ['Return the balance.'], 'obligations': ['Handle unknown accounts.']}
            with (self.root / path).open('a') as stream:
                if role == 'provided': stream.write('\n' + block('concorde-contract', definition))
                stream.write('\n' + block('concorde-contract-binding', binding))
        r = self.repository()
        self.assertEqual((), r.contracts(r.select('service.transfer')))
        self.assertEqual('module.ledger', r.context_contracts(r.select('service.transfer'))[0]['owner'])
        self.assertEqual('success', validate_repository(self.root, package_root=PACKAGE).status)
        self.registry['targets'][2]['references'] = []
        self.save()
        self.assertIn('CONCORDE-CONTRACT-002', {f.rule_id for f in validate_repository(self.root, package_root=PACKAGE).findings})

    def test_old_wire_payloads_are_not_reinterpreted(self):
        value = typed('concorde-context-snapshot', resolve_context(self.repository(), 'scope.bank').value)
        self.assertEqual(2, value['schema_version'])
        value['schema_version'] = 1
        with self.assertRaises(TypedDataError): validate_typed(value)

    def test_reviewer_attributes_foreign_definition_to_owner_and_gap_to_consumer(self):
        self.reference('service.transfer', 'module', 'module.ledger')
        def callback(stage, snapshot, result, cwd):
            if stage == 'spec-review':
                result.update(status='findings', findings=[{
                    'id': 'finding.provider', 'severity': 'advisory', 'target_id': 'module.ledger',
                    'document': 'specs/ledger/module.md', 'contract': 'scenario.ledger.read',
                    'location': {'path': 'specs/ledger/module.md', 'line': 1},
                    'problem': 'Clarify the return description.', 'affected_task': 'Read a balance'}])
        double = ModelProcessDouble(callback)
        host = CapabilityHost(self.root, PACKAGE, executor=double.executor, allow_primary_worktree=True)
        result = run_capability('concorde-review', CONFIGURATION, typed('concorde-review-request', {
            'target_id': 'service.transfer', 'task': 'Review balance reads', 'review_mode': 'spec'}), host_context=host)
        self.assertEqual('succeeded', result['status'], result)
        review = result['output']['data']['reviews'][0]['data']
        self.assertEqual('service.transfer', review['target_id'])
        self.assertEqual('module.ledger', review['findings'][0]['target_id'])
        self.assertTrue(all(not item['write_paths'] for item in host.descriptions))

    def test_required_binding_links_report_excluded_definition_without_adding_context(self):
        path = self.root / 'specs/transfer/module.md'
        path.write_text(path.read_text() + '\n' + block('concorde-contract-binding', {
            'id': 'contract.missing', 'version': 1, 'role': 'required', 'peer': 'module.ledger',
            'selection_condition': 'When reading.', 'relied_upon_guarantees': [
                '[Read](../ledger/module.md#scenario.ledger.read)'], 'obligations': ['Handle missing accounts.']}))
        result = validate_repository(self.root, package_root=PACKAGE)
        gap = next(f for f in result.findings if f.rule_id == 'CONCORDE-CONTEXT-001')
        self.assertIn('module.ledger', gap.message)
        self.assertEqual('service.transfer', gap.subject_id)
        self.assertNotIn('specs/ledger/module.md', self.repository().spec_files('service.transfer'))

    def test_invalid_query_kinds_and_duplicate_ownership_are_rejected(self):
        r = self.repository()
        for identity in ('document.bank', 'req.transfer.pure', 'entity.ledger.store', 'specs/bank/module.md'):
            with self.subTest(identity=identity), self.assertRaises(SpecError) as caught:
                r.spec_files(identity)
            self.assertEqual('invalid_target', caught.exception.code)
        self.registry['targets'][0]['documents'].append('specs/transfer/promises.md')
        self.save()
        with self.assertRaisesRegex(SpecError, 'one owner'):
            self.repository()

    def test_transfer_and_provider_inventory_compare_old_and_candidate_consumers(self):
        self.reference('scope.bank', 'module', 'service.transfer')
        self.reference('module.ledger', 'document', 'document.transfer.promises')
        old = self.repository()
        old.context_identities()
        self.registry['targets'][2]['documents'].remove('specs/transfer/promises.md')
        self.registry['targets'][1]['documents'].append('specs/transfer/promises.md')
        path = self.root / 'specs/transfer/promises.md'
        path.write_bytes(path.read_bytes().replace(b'"service.transfer"', b'"scope.audit"'))
        self.save()
        self.assertEqual(('module.ledger', 'scope.audit', 'scope.bank', 'service.transfer'),
                         old.affected_contexts(self.repository()))
