# Dogfood scenarios requirements

The Module-wide obligations of [Dogfood scenarios](module.md). The [scenarios](scenarios.md) show
them in concrete situations.

### req.dogfood-scenarios.checkout-untouched — The checkout is never made faulty

The runner SHALL apply a fault only to the scenario's own clone of Concorde, never to the checkout
it runs from.

### req.dogfood-scenarios.fault-exact — A fault applies exactly or not at all

The runner SHALL refuse a fault whose old text of an edit is not found exactly once, naming the
edit and file, before committing anything.

### req.dogfood-scenarios.judged-from-files — The evaluation reads files, not the session

The evaluation SHALL decide every check from files and command results in the scenario directory,
never from the session's messages.
