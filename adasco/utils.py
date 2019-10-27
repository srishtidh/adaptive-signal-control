def round_to_delta(time, resolution=0.1):
    return round(time / resolution) * resolution


def slice(departures, start, end):
    result = []
    for departure in departures:
        if departure.time > end:
            break
        if departure.time >= start:
            result.append(departure)
    return result
