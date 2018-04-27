from redshift import Interpolater

i = Interpolater()
i.interpolate('01:15')

i.interpolate_value(0, 100, .5)
