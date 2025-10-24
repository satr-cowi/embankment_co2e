import numpy as np

def calc_emb_area(h, path_width, slope_grad):
    
    w_top = path_width
    w_bot = path_width + h*2*slope_grad
    
    w_av = (w_top+w_bot)/2
    
    return w_av*h


def calc_co2e(area, ECF_soil, ECF_geogrid=None):
    """_summary_

    Assumes 1m spacing for geogrids.

    Parameters
    ----------
    area : _type_
        _description_
    ECF_soil : _type_
        _description_
    ECF_geogrid : int, optional
        _description_, by default None
    """
    
    # 1m spacing assumption
    geo_L = area
    
    if ECF_geogrid is None:
        ECF_geo = np.array([0,1.88,2.88,5.01])
    
    return area[:,None] * ECF_soil + geo_L[:,None] * ECF_geo[None,:]

def calc_carbon_per_FA(h,path_width,slope_grad,ECF_soil,ECF_geogrid=None):
    area = calc_emb_area(h,path_width,slope_grad)
    co2 = calc_co2e(area,ECF_soil,ECF_geogrid)
    return co2/path_width