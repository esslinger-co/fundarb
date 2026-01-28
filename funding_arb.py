from dataclasses import dataclass
from typing import List, Literal, TypedDict


Position = Literal["long", "short"]


@dataclass
class Leg:
    """
    Repräsentiert einen einzelnen Leg in einer Funding-Struktur.
    - name: frei wählbar, z. B. "Binance Perp"
    - position: "long" oder "short"
    - funding_rate: pro Intervall, z. B. 0.0171 = 1.71 %
    - notional: USD/USDT-Wert der Position
    """
    name: str
    position: Position
    funding_rate: float
    notional: float

    def __post_init__(self) -> None:
        p = self.position.lower()
        if p not in ("long", "short"):
            raise ValueError(f"Position muss 'long' oder 'short' sein, nicht: {self.position}")
        if self.notional < 0:
            raise ValueError("Notional muss >= 0 sein.")
        # Normalisiere Position intern
        self.position = p  # type: ignore[assignment]

    @property
    def pnl_per_interval(self) -> float:
        """
        Konvention:
        - Positive funding_rate: Longs zahlen Shorts.
        - Long-Position: zahlt funding_rate * notional.
        - Short-Position: erhält funding_rate * notional.
        """
        if self.position == "long":
            return -self.funding_rate * self.notional
        else:  # "short"
            return self.funding_rate * self.notional


class FundingResult(TypedDict):
    pnl_per_interval: float
    pnl_per_day: float
    pnl_per_year: float
    long_notional: float
    short_notional: float
    delta: float
    neutral: bool


def funding_arb(legs: List[Leg], interval_hours: float = 8.0) -> FundingResult:
    """
    Kernfunktion: Berechnet Funding-PnL und Delta-Neutralität.

    Args:
        legs: Liste von Leg-Objekten (Spot, Perps, etc.).
        interval_hours: Dauer eines Funding-Intervalls (z. B. 8.0).

    Returns:
        dict mit PnL pro Intervall, Tag, Jahr und Delta-Infos.
    """
    if interval_hours <= 0:
        raise ValueError("interval_hours muss > 0 sein.")

    total_pnl = sum(l.pnl_per_interval for l in legs)

    long_notional = sum(l.notional for l in legs if l.position == "long")
    short_notional = sum(l.notional for l in legs if l.position == "short")
    delta = long_notional - short_notional

    intervals_per_day = 24.0 / interval_hours
    pnl_day = total_pnl * intervals_per_day
    pnl_year = pnl_day * 365.0

    return FundingResult(
        pnl_per_interval=total_pnl,
        pnl_per_day=pnl_day,
        pnl_per_year=pnl_year,
        long_notional=long_notional,
        short_notional=short_notional,
        delta=delta,
        neutral=abs(delta) < 1e-6,
    )


def pretty_print(result: FundingResult) -> None:
    """
    Optionale, reine Ausgabe-Funktion.
    Kannst du nutzen oder ignorieren – Logik bleibt getrennt.
    """
    print("=== Funding-Arbitrage Ergebnis ===")
    print(f"Neutral        : {result['neutral']}")
    print(f"Delta          : {result['delta']:.2f}")
    print(f"Long-Notional  : {result['long_notional']:.2f}")
    print(f"Short-Notional : {result['short_notional']:.2f}")
    print()
    print(f"PnL/Intervall  : {result['pnl_per_interval']:.2f}")
    print(f"PnL/Tag        : {result['pnl_per_day']:.2f}")
    print(f"PnL/Jahr       : {result['pnl_per_year']:.2f}")


if __name__ == "__main__":
    # Minimaler Demo-Block – kannst du löschen, auskommentieren oder anpassen.
    legs = [
        Leg("Spot", "long", 0.0, 10_000),
        Leg("Perp", "short", 0.0171, 10_000),
    ]
    result = funding_arb(legs, interval_hours=8.0)
    pretty_print(result)
