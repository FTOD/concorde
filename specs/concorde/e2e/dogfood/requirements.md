# Dogfood scenarios requirements

The Module-wide obligations of [Dogfood scenarios](module.md). The [scenarios](scenarios.md) show
them in concrete situations.

### req.dogfood-scenarios.checkout-untouched — The checkout is never made faulty

The runner SHALL apply a fault only to the scenario's own clone of Concorde, never to the checkout
it runs from.

### req.dogfood-scenarios.fault-exact — A fault that no longer applies exactly is refused

The runner SHALL refuse a fault whose old text of an edit is not found exactly once, naming the
edit, its file and how often the old text was found, before committing anything.

### req.dogfood-scenarios.judged-from-files — The evaluation reads files, not the session

The evaluation SHALL decide every check from the files of the
scenario directory and the results of commands run
on them, never from the session's messages.
