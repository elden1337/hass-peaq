from peaqevcore.models.fuses import Fuses

DISABLED = "Disabled"
CRITICAL = "Critical!"
WARNING = "Warning!"
OK = "Ok"
CUTOFF_THRESHOLD = 0.9
WARNING_THRESHOLD = 0.75

FUSES_DICT = {
        Fuses.FUSE_3_16: 11000,
        Fuses.FUSE_3_20: 14000,
        Fuses.FUSE_3_25: 17000,
        Fuses.FUSE_3_35: 24000,
        Fuses.FUSE_3_50: 35000,
        Fuses.FUSE_3_63: 44000,
        Fuses.DEFAULT:   0
    }

FUSES_MAX_SINGLE_FUSE = {
    Fuses.FUSE_3_16: 16,
    Fuses.FUSE_3_20: 20,
    Fuses.FUSE_3_25: 25,
    Fuses.FUSE_3_35: 35,
    Fuses.FUSE_3_50: 50,
    Fuses.FUSE_3_63: 63
}

FUSES_LIST = [f.value for f in Fuses]

