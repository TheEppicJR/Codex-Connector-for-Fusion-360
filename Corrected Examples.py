"""
Create a new sketch on the yz plane called base profile
"""
sketches = hub.sketches
basePlane = hub.yZConstructionPlane
baseProfile = sketches.add(basePlane)
baseProfile.name = 'Base Profile'

"""
make a circle on the sketch that has a diameter of 15mm
"""
diameter = 15/10
baseProfile.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0,0,0), diameter)

"""
Extrude that circle up 4.5 inches
"""
profiles = baseProfile.profiles
baseCircle = profiles.item(0)
extrudes = hub.features.extrudeFeatures
extInput = extrudes.createInput(baseCircle, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
distance = adsk.core.ValueInput.createByString("4.5 in")
extInput.setDistanceExtent(False, distance)
ext = extrudes.add(extInput)
