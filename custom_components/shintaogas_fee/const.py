"""Constants of the ShinTao Gas Fee component."""

DEFAULT_NAME = "ShinTao Gas Fee"
DEFAULT_NAME_UPLOAD_USAGE = "ShinTao Gas Upload Usage"
DOMAIN = "shintaogas_fee"
DOMAINS = [ "sensor", "binary_sensor" ]
DATA_KEY = "sensor.shintaogas_fee"
DATA_KEY_BINARY = "binary_sensor.shintao_gas_upload_usage"

ATTR_BILLING_MONTH = "billing_month"
ATTR_CURRENT_GASMETER = "current_gasmeter"
ATTR_PAYMENT = "gas_payment"
ATTR_GAS_CONSUMPTION = "gas_consumption"
ATTR_BILLING_GAS = "billing_gas"
ATTR_BILL_AMOUNT = "billing_amount"
ATTR_HTTPS_RESULT = "https_result"
ATTR_UPLOAD_DATETIME = "upload_datetime"
ATTR_USAGE = "usage"
ATTR_LIST = [
    ATTR_BILLING_MONTH,
    ATTR_CURRENT_GASMETER,
    ATTR_PAYMENT,
    ATTR_GAS_CONSUMPTION,
    ATTR_BILLING_GAS,
    ATTR_BILL_AMOUNT,
    ATTR_HTTPS_RESULT
]

CONF_GASID = "gasid"
CONF_COOKIE = "cookie"
# 5308 characters
CONF_VIEWSTATE = "viewstate"
# 668 characters
CONF_VIEWSTATEGENERATOR = "viewstategenerator"
CONF_EVENTVALIDATION = "eventvalidatioin"
# 636 characters
CONF_VIEWSTATE4UPLOAD = "viewstate4upload"
ATTRIBUTION = "Powered by ShinTao Gas Data"
MANUFACTURER = "ShinTao Gas"

HA_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36 OPR/38.0.2220.41"
BASE_URL = 'https://www.shintaogas.com.tw/Home/service/form-6.aspx'

REQUEST_TIMEOUT = 10  # seconds
