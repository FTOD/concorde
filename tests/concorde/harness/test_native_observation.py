"""Nonsecret passive diagnostic mechanics; actual native publication has its own opt-in probes."""

import subprocess
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


class NativeObservationTests(unittest.TestCase):
    def test_sdk_facade_delegates_unchanged_and_observes_effective_session_without_auth(
        self,
    ):
        code = r"""
import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
import {nativeObservation} from './tests/concorde/harness/native_observation.mjs';
const root=fs.mkdtempSync(path.join(os.tmpdir(),'native-observation-unit-'));
try {
 const events=[];let prompt='structured_output';const value={session:{sessionId:'fixture',getAllTools:()=>[{name:'structured_output',parameters:{type:'object'}}],getActiveToolNames:()=>['structured_output'],get systemPrompt(){return prompt},model:{provider:'fixture',id:'model',apiKey:'MUST_NOT_RECORD_AUTH'},subscribe(f){events.push(f)}}};
 const options={cwd:root,modelRuntime:{credentials:'MUST_NOT_RECORD_AUTH'}};
 const observer=nativeObservation(root);const sdk=observer.sdk({createAgentSession:async input=>{assert.equal(input,options);return value}});
 assert.equal(await sdk.createAgentSession(options),value);
 prompt='Effective structured_output prompt';events[0]({type:'agent_start'});
 const raw=fs.readFileSync(path.join(root,'session-0.json'),'utf8');const record=JSON.parse(raw);
 assert.equal(record.executionStarts,1);assert.equal(record.systemPrompt,prompt);assert(record.active.includes('structured_output'));assert(!raw.includes('MUST_NOT_RECORD_AUTH'));
 assert.equal(fs.statSync(path.join(root,'session-0.json')).mode & 0o777,0o600);
 prompt='Terminal prompt reset';events[0]({type:'agent_end'});
 assert.equal(JSON.parse(fs.readFileSync(path.join(root,'session-0-start-1.json'),'utf8')).systemPrompt,'Effective structured_output prompt');
} finally {fs.rmSync(root,{recursive:true,force:true})}
"""
        result = subprocess.run(
            ["node", "--input-type=module", "-e", code],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
