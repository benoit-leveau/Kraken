
from kraken import plugins
from kraken.core.maths import Xfo, Vec3, Quat
from kraken.core.profiler import Profiler
from kraken_examples.clavicle_component import ClavicleComponentGuide, ClavicleComponentRig
from kraken.helpers.utility_methods import logHierarchy
import json


Profiler.getInstance().push("clavicle_build")

clavicleGuide = ClavicleComponentGuide("clavicle")
clavicleGuide.loadData({
        "name": "Clavicle",
        "location": "L",
        "clavicleXfo": Xfo(Vec3(0.1322, 15.403, -0.5723)),
        "clavicleUpVXfo": Xfo(Vec3(0.0, 1.0, 0.0)),
        "clavicleEndXfo": Xfo(Vec3(2.27, 15.295, -0.753))
    })

# Save the clavicle guid data for persistence.
saveData = clavicleGuide.saveData()

clavicleGuideData = clavicleGuide.getRigBuildData()

clavicle = ClavicleComponentRig()
clavicle.loadData(clavicleGuideData)

builder = plugins.getBuilder()
builder.build(clavicle)

Profiler.getInstance().pop()

if __name__ == "__main__":
    print Profiler.getInstance().generateReport()
else:
    logHierarchy(clavicle)