"""Support for the ShinTao Gas Fee."""
import logging
from typing import Callable
from datetime import timedelta

from aiohttp.hdrs import USER_AGENT
import requests
from bs4 import BeautifulSoup

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity
from homeassistant.util import Throttle
import homeassistant.util.dt as dt_util
from homeassistant.helpers.event import track_point_in_time
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CURRENCY_DOLLAR,
    HTTP_OK,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
)
from .const import (
    ATTRIBUTION,
    ATTR_CURRENT_GASMETER,
    ATTR_BILLING_MONTH,
    ATTR_PAYMENT,
    ATTR_GAS_CONSUMPTION,
    ATTR_BILLING_GAS,
    ATTR_BILL_AMOUNT,
    ATTR_HTTPS_RESULT,
    ATTR_LIST,
    BASE_URL,
    CONF_GASID,
    CONF_COOKIE,
    CONF_VIEWSTATE,
    CONF_VIEWSTATEGENERATOR,
    CONF_EVENTVALIDATION,
    DATA_KEY,
    DEFAULT_NAME,
    DOMAIN,
    HA_USER_AGENT,
    MANUFACTURER,
    REQUEST_TIMEOUT
)

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_FORCED_UPDATES = timedelta(hours=12)
MIN_TIME_BETWEEN_UPDATES = timedelta(hours=24)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_devices: Callable
) -> None:
    """Set up the ShinTao Gas Fee Sensor from config."""
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    cookie = None
    if config.data.get(CONF_GASID, None):
        gasid = config.data[CONF_GASID]
        viewstate = config.data[CONF_VIEWSTATE]
        viewstategenerator = config.data[CONF_VIEWSTATEGENERATOR]
        eventvalidation = config.data[CONF_EVENTVALIDATION]
    else:
        gasid = config.options[CONF_GASID]
        viewstate = config.options[CONF_VIEWSTATE]
        viewstategenerator = config.options[CONF_VIEWSTATEGENERATOR]
        eventvalidation = config.options[CONF_EVENTVALIDATION]

    data = ShinhuGasFeeData(gasid, cookie, viewstate, viewstategenerator, eventvalidation)
    data.expired = False
    device = ShinhuGasFeeSensor(data, gasid)

    hass.data[DATA_KEY][config.entry_id] = device
    async_add_devices([device], update_before_add=True)


class ShinhuGasFeeData():
    """Class for handling the data retrieval."""

    def __init__(self, gasid, cookie, viewstate, viewstategenerator, eventvalidation):
        """Initialize the data object."""
        self.data = {}
        self._gasid = gasid
        self._cookie = cookie
        self._viewstate = viewstate
        self._viewstategenerator = viewstategenerator
        self._eventvalidation = eventvalidation
        self.expired = False
        self.uri = BASE_URL

    def _parser_html(self, text):
        """ parser html """
        data = {}
        text = text.replace("<br>", "").replace("\n", "").replace("\r", "")
        soup = BeautifulSoup(text, 'html.parser')
        billdetail = soup.find(id="divSearchData")
        if billdetail:
            results = billdetail.find_all("td", limit=40)
            if results and len(results) >= 40:
                for i in range(3, 17):
                    data[results[i].string.replace(" ", "")] = results[i + 14].string
        return data

    def update_no_throttle(self):
        """Get the data for a specific gas id."""
        self.update(no_throttle=True)

    @Throttle(MIN_TIME_BETWEEN_UPDATES, MIN_TIME_BETWEEN_FORCED_UPDATES)
    def update(self, **kwargs):
        """Get the latest data for gas id from REST service."""
        headers = {USER_AGENT: HA_USER_AGENT}
        payload = {
            "txtKey": self._gasid,
            "__VIEWSTATE": self._viewstate,
            "__VIEWSTATEGENERATOR": self._viewstategenerator,
            "__EVENTVALIDATION": self._eventvalidation,
            "imgBtnSearch.x": '9',
            "imgBtnSearch.y": '11'
        }

        self.data = {}
        self.data[self._gasid] = {}

        if not self.expired:
            try:
                req = requests.post(
                    self.uri,
                    headers=headers,
                    data=payload,
                    timeout=REQUEST_TIMEOUT)

            except requests.exceptions.RequestException:
                _LOGGER.error("Failed fetching data for %s", self._gasid)
                return

            if req.status_code == HTTP_OK:
                self.data[self._gasid] = self._parser_html(req.text)
                if len(self.data[self._gasid]) >= 1:
                    self.data[self._gasid]['result'] = HTTP_OK
                else:
                    self.data[self._gasid]['result'] = HTTP_NOT_FOUND
                self.expired = False
            elif req.status_code == HTTP_NOT_FOUND:
                self.data[self._gasid]['result'] = HTTP_NOT_FOUND
                self.expired = True
            else:
                info = ""
                self.data[self._gasid]['result'] = req.status_code
                if req.status_code == HTTP_FORBIDDEN:
                    info = " Token or Cookie is expired"
                _LOGGER.error(
                    "Failed fetching data for %s (HTTP Status_code = %d).%s",
                    self._gasid,
                    req.status_code,
                    info
                )
                self.expired = True
        else:
            self.data[self._gasid]['result'] = 'sessions_expired'
            _LOGGER.warning(
                "Failed fetching data for %s (Sessions expired)",
                self._gasid,
            )


class ShinhuGasFeeSensor(SensorEntity):
    """Implementation of a ShinTao Gas Fee sensor."""

    def __init__(self, data, gasid):
        """Initialize the sensor."""
        self._state = None
        self._data = data
        self._attributes = {}
        self._attr_value = {}
        self._name = "{} {}".format(DEFAULT_NAME, gasid)
        self._gasid = gasid

        self.uri = BASE_URL
        for i in ATTR_LIST:
            self._attr_value[i] = None
        self._data.data[self._gasid] = {}
        self._data.data[self._gasid]['result'] = None

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._name

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:currency-twd"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return CURRENCY_DOLLAR

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        self._attributes[ATTR_ATTRIBUTION] = ATTRIBUTION
        for i in ATTR_LIST:
            self._attributes[i] = self._attr_value[i]
        return self._attributes

    @property
    def device_info(self):
        return {
            'identifiers': {(DOMAIN, self._gasid)},
            'manufacturer': MANUFACTURER,
            'name': self._name
        }

    async def async_added_to_hass(self):
        """Get initial data."""
        # To make sure we get initial data for the sensors ignoring the normal
        # throttle of 45 mintunes but using an update throttle of 15 mintunes
        self.hass.async_add_executor_job(self.update_nothrottle)

    def update_nothrottle(self, dummy=None):
        """Update sensor without throttle."""
        self._data.update_no_throttle()

        # Schedule a forced update 15 mintunes in the future if the update above
        # returned no data for this sensors power number.
        if not self._data.expired:
            track_point_in_time(
                self.hass,
                self.update_nothrottle,
                dt_util.now() + MIN_TIME_BETWEEN_FORCED_UPDATES,
            )
            return

        self.schedule_update_ha_state()

    async def async_update(self):
        """Update state."""
        self.hass.async_add_executor_job(self._data.update)
        if self._gasid in self._data.data:
            for i, j in self._data.data[self._gasid].items():
                if i == None:
                    continue
                i = i.replace("\r", "").replace("\n", "")
                if i is None:
                    continue
                if "\u7e3d\u91d1\u984d" in i:
                    self._state = ''.join(k for k in j if k.isdigit() or k == ".")
                    self._attr_value[ATTR_BILL_AMOUNT] = j
                if "\u9650\u7e73\u65e5" in i:
                    self._attr_value[ATTR_BILLING_MONTH] = j
                if "\u6307\u91dd\u5ea6\u6578" in i:
                    self._attr_value[ATTR_CURRENT_GASMETER] = j
                if "\u7e73\u8cbb\u65e5" in i:
                    self._attr_value[ATTR_PAYMENT] = j
                if "\u4f7f\u7528\u5ea6" in i:
                    self._attr_value[ATTR_GAS_CONSUMPTION] = j
                if "\u8a08\u8cbb\u5EA6" in i:
                    self._attr_value[ATTR_BILLING_GAS] = j
            self._attr_value[ATTR_HTTPS_RESULT] = self._data.data[self._gasid].get(
                'result', 'Unknow')
            if self._attr_value[ATTR_HTTPS_RESULT] == HTTP_FORBIDDEN:
                self._state = None
