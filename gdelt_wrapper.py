import gdelt

def query():
    gd = gdelt.gdelt(version=2)
    results = gd.Search('Mar 19, 2021',table='events',coverage=True)
    return results


if __name__ == "__main__":
    df = query()
    df.to_pickle("march19events.pkl")