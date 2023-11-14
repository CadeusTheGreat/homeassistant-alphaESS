"""Coordinator for AlphaEss integration."""
import datetime
import json
import logging

import aiohttp
from alphaess import alphaess

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER: logging.Logger = logging.getLogger(__package__)


class AlphaESSDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: alphaess.alphaess) -> None:
        """Initialize."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.api = client
        self.update_method = self._async_update_data
        self.data: dict[str, dict[str, float]] = {}

    async def _async_update_data(self):
        """Update data via library."""
        try:
            jsondata: json = await self.api.getdata()
            for invertor in jsondata:

                inverterdata: dict[str, any] = {}
                inverterdata.update({"Model": invertor.get("minv")})
                
                # data from summary data API
                _sumdata = invertor.get("SumData", {})
                # data from one date energy API
                _onedateenergy = invertor.get("OneDateEnergy", {})
                # data from last power data API
                _powerdata = invertor.get("LastPower", {})
                _gridpowerdetails = _powerdata.get("pgridDetail",{})
                _pvpowerdetails = _powerdata.get("ppvDetail",{})

                _pv =  _onedateenergy.get("epv")
                _feedin = _onedateenergy.get("eOutput")
                _gridcharge = _onedateenergy.get("eGridCharge")
                _charge = _onedateenergy.get("eCharge")
                _soc = _powerdata.get("soc")
                
                inverterdata.update({"Solar Production": _sumdata.get("epvtoday")})
                inverterdata.update({"Total Load": _sumdata.get("eload")})
                inverterdata.update({"Grid to Load": _sumdata.get("einput")})
                inverterdata.update({"Charge": _sumdata.get("echarge")})
                inverterdata.update({"Discharge": _sumdata.get("edischarge")})
                inverterdata.update({"Solar to Grid": _sumdata.get("eoutput")})              
                inverterdata.update({"Solar to Battery": _charge - _gridcharge})
                inverterdata.update({"Solar to Load": _pv - _feedin})
                inverterdata.update({"Grid to Battery": _gridcharge})
                inverterdata.update({"EV Charger": _onedateenergy.get("eChargingPile")})           
                inverterdata.update({"Instantaneous Generation": _powerdata.get("ppv")})
                inverterdata.update({"Instantaneous PPV1": _pvpowerdetails.get("ppv1")})
                inverterdata.update({"Instantaneous PPV2": _pvpowerdetails.get("ppv2")})
                inverterdata.update({"Instantaneous PPV3": _pvpowerdetails.get("ppv3")})
                inverterdata.update({"Instantaneous PPV4": _pvpowerdetails.get("ppv4")})
                inverterdata.update({"Instantaneous Battery SOC": _soc})
                inverterdata.update({"State of Charge": _soc})
                inverterdata.update({"Instantaneous Battery I/O": _powerdata.get("pbat")})
                inverterdata.update({"Instantaneous Grid I/O Total": _powerdata.get("pgrid")})
                inverterdata.update({"Instantaneous Grid I/O L1": _gridpowerdetails.get("pmeterL1")})
                inverterdata.update({"Instantaneous Grid I/O L2": _gridpowerdetails.get("pmeterL2")})
                inverterdata.update({"Instantaneous Grid I/O L3": _gridpowerdetails.get("pmeterL3")})
                inverterdata.update({"Instantaneous Load": _powerdata.get("pload")})



                self.data.update({invertor["sysSn"]: inverterdata})

            return self.data
        except (
            aiohttp.client_exceptions.ClientConnectorError,
            aiohttp.ClientResponseError,
        ) as error:
            raise UpdateFailed(error) from error
