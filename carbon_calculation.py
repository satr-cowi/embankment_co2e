"""
Simple file to hold useful calculation functions.

"""
import numpy as np

def _calc_emb_area(h, path_width, slope_grad):
    """Calculates the cross secitonal area of the assumed embankment.

    Parameters
    ----------
    h : float or numpy array of floats
        Embankment height
    path_width : float or numpy array of floats
        Width of the path
    slope_grad : float or numpy array of floats
        Gradient of the side slopes

    Returns
    -------
    float or numpy array of floats
        Area of embankment
    """
    w_top = path_width
    w_bot = path_width + h*2*slope_grad
    
    w_av = (w_top+w_bot)/2
    
    return w_av*h

def calc_ECF_from_distance(distance, carbon_per_km_per_m3, processing_factor):
    """Returns the embodied carbon per m3 of soil.

    Parameters
    ----------
    distance : float or numpy array of floats
        Transport distance
    carbon_per_km_per_m3 : float or numpy array of floats
        ECF of transporting soil (per km per m3)
    processing_factor : float or numpy array of floats
        ECF for excavation/filling

    Returns
    -------
    float or numpy array of floats
        Total ECF for transport and installation
    """
    return processing_factor + distance*carbon_per_km_per_m3
    

def _calc_co2e(area, ECF_soil, ECF_geogrid):
    """_summary_

    Assumes 1m spacing for geogrids.

    Parameters
    ----------
    area : float
        Cross sectional area of embankment
    ECF_soil : float
        The total ECF for soil
    ECF_geogrid : np array of floats, optional
        The ECF for a m2 of geogrid, by default None
    """
    
    # 1m spacing assumption
    geo_L = area
    return area[:,None] * ECF_soil + geo_L[:,None] * ECF_geogrid[None,:]

def calc_carbon_per_FA(h,path_width,slope_grad,ECF_soil,ECF_geogrid=np.array([0])):
    """Calculate the CO2e per functional area for an embankment.

    Parameters
    ----------
    h : float
        Embankment height
    path_width : float
        Embankment width at top
    slope_grad : float
        Embankment slope gradient
    ECF_soil : float
        Total ECF for soil. See `calc_ECF_from_distance`.
    ECF_geogrid : numpy array of floats, optional
        Range of values e.g. (min, average, max) to consider for ECF of geogrid per m2.
        By default np.array([0])

    Returns
    -------
    numpy array of floats
        _description_
    """
    area = _calc_emb_area(h,path_width,slope_grad)
    co2 = _calc_co2e(area,ECF_soil,ECF_geogrid)
    return co2/path_width