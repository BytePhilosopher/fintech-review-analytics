"""Bank app configuration for Google Play review scraping."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BankApp:
    """Google Play app metadata for a bank mobile application."""

    package_id: str
    bank_name: str
    display_name: str


# Three Ethiopian bank apps on Google Play
BANK_APPS: tuple[BankApp, ...] = (
    BankApp(
        package_id="com.combanketh.mobilebanking",
        bank_name="Commercial Bank of Ethiopia",
        display_name="Commercial Bank of Ethiopia Mobile",
    ),
    BankApp(
        package_id="com.dashen.dashensuperapp",
        bank_name="Dashen Bank",
        display_name="Dashen Bank Super App",
    ),
    BankApp(
        package_id="com.boa.boaMobileBanking",
        bank_name="Bank of Abyssinia",
        display_name="BoA Mobile",
    ),
)

# Awash-Online (pegasus.project.awash.mobile.android.bundle.mobilebank) exposes
# only ~128 reviews via the Google Play API; BoA Mobile is used instead.

SOURCE = "Google Play"
MIN_REVIEWS_PER_BANK = 400
DEFAULT_LANG = "en"
DEFAULT_COUNTRY = "us"
BATCH_SIZE = 200
