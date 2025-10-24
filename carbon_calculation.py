import numpy as np

def calc_emb_area(h, path_width, slope_grad):
    
    w_top = path_width
    w_bot = path_width + h*2*slope_grad
    
    w_av = (w_top+w_bot)/2
    
    return w_av*h

def calc_ECF_from_distance(distance, carbon_per_km_per_m3, processing_factor):
    return processing_factor + distance*carbon_per_km_per_m3
    

def calc_co2e(area, ECF_soil, ECF_geogrid):
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
    return area[:,None] * ECF_soil + geo_L[:,None] * ECF_geogrid[None,:]

def calc_carbon_per_FA(h,path_width,slope_grad,ECF_soil,ECF_geogrid=np.array([0])):
    area = calc_emb_area(h,path_width,slope_grad)
    co2 = calc_co2e(area,ECF_soil,ECF_geogrid)
    return co2/path_width