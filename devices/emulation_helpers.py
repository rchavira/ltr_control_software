import random
from os import path


def gen_bool_values(values_file, qty, percent_true):
    perc = percent_true if percent_true > 0 else int(percent_true * 100)
    with open(values_file, "w") as f:
        for _ in range(qty):
            rval = random.randint(0, 100)
            v = 0 if rval < perc else 1
            f.write(f"{v}\n")


def gen_values(values_file, r_min, r_max, qty, isfloat=True):
    with open(values_file, "w") as f:
        for _ in range(qty):
            if isfloat:
                v = random.uniform(r_min, r_max)
            else:
                v = random.randint(r_min, r_max)
            f.write(f"{v}\n")


def gen_ramp_up(values_file, r_min, r_max, qty, isfloat=True):
    g_range = int(r_max - r_min)
    step = g_range / qty
    l_max = r_min + step
    with open(values_file, "w") as f:
        for _ in range(qty):
            v = random.uniform(l_max - step, l_max) if isfloat else random.randint(int(l_max - step), int(l_max))
            f.write(f"{v}\n")
            l_max += step


def gen_ramp_down(values_file, r_min, r_max, qty, isfloat=True):
    g_range = int(r_max - r_min)
    step = g_range / qty
    l_max = r_max - step
    with open(values_file, "w") as f:
        for _ in range(qty):
            v = random.uniform(l_max - step, l_max) if isfloat else random.randint(int(l_max - step), int(l_max))
            f.write(f"{v}\n")
            l_max -= step


def gen_up_and_down(values_file, r_min, r_max, qty, isfloat=True):
    g_range = int(r_max - r_min)
    step = g_range / (qty / 2)
    l_max = r_min + step
    with open(values_file, "w") as f:
        for _ in range(qty):
            v = random.uniform(l_max - step, l_max) if isfloat else random.randint(int(l_max - step), int(l_max))
            f.write(f"{v}\n")
            l_max += step

        l_max = r_max - step
        for _ in range(qty):
            v = random.uniform(l_max - step, l_max) if isfloat else random.randint(int(l_max - step), int(l_max))
            f.write(f"{v}\n")
            l_max -= step


def get_value_from_file(fname):
    with open(fname, "r") as f:
        values = f.readlines()

    v = values[0]
    del values[0]
    values.append(v)

    with open(fname, "w") as f:
        for line in values:
            f.write(f"{line}")

    return v


def get_next_float(values_file):
    """
    Get the next float value from local file.  This routine will cycle through a file,
    appending used values to the end of the file.
    :param values_file: file to read values from
    :return: float value of a single line read from the file.
    """
    value = 0.0

    if path.exists(values_file):
        value = float(get_value_from_file(values_file))

    return value


def get_next_int(values_file):
    """
    Get the next int value from local file.  This routine will cycle through a file,
    appending used values to the end of the file.
    :param values_file: file to read values from
    :return: int value of a single line read from the file.
    """
    value = 0
    if path.exists(values_file):
        value = int(get_value_from_file(values_file))

    return value