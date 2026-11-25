"""Build-time: generate the data antiSMASH derives inside its own package (classifier
pickles, alignment caches, CSS, pressed HMMs). The image runs as the host user and is
recreated per command, so this cannot happen lazily at run time. Modules whose data
lives in the database directory are prepared by `flanders reference fetch` instead.
"""

from antismash.config import build_config
from antismash.main import get_all_modules

build_config(["--databases", "/tmp/no-databases"], isolated=True, modules=get_all_modules())
prepared, deferred = [], []
for module in get_all_modules():
    if not hasattr(module, "prepare_data"):
        continue
    name = module.__name__.split(".")[-1]
    try:
        module.prepare_data(False)
        prepared.append(name)
    except Exception as exc:  # needs the downloaded databases; done at reference fetch
        deferred.append(f"{name} ({type(exc).__name__})")
print("antiSMASH data prepared:", ", ".join(prepared))
print("deferred to reference fetch:", ", ".join(deferred))
