"""Swissmetro dataset loader."""

from dataclasses import dataclass
import pandas as pd
from circe.data.download import ensure_swissmetro


@dataclass
class SwissmetroRecord:
    record_id: int
    choice: int
    purpose: int
    income: int
    train_tt: float
    train_cost: float
    train_he: float
    sm_tt: float
    sm_cost: float
    sm_he: float
    car_tt: float
    car_cost: float


def load_swissmetro() -> list[SwissmetroRecord]:
    path = ensure_swissmetro()
    df = pd.read_csv(path, sep="\t")
    df = df[(df["PURPOSE"].isin([1, 3])) & (df["CHOICE"] != 0)]
    records = []
    for idx, row in df.iterrows():
        records.append(SwissmetroRecord(
            record_id=int(idx),
            choice=int(row["CHOICE"]),
            purpose=int(row["PURPOSE"]),
            income=int(row["INCOME"]),
            train_tt=row["TRAIN_TT"],
            train_cost=row["TRAIN_CO"] * (row["GA"] == 0),
            train_he=row["TRAIN_HE"],
            sm_tt=row["SM_TT"],
            sm_cost=row["SM_CO"] * (row["GA"] == 0),
            sm_he=row["SM_HE"],
            car_tt=row["CAR_TT"],
            car_cost=row["CAR_CO"],
        ))
    return records
