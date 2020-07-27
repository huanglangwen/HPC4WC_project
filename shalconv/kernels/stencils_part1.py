import gt4py as gt
from gt4py import gtscript
from gt4py.__gtscript__ import PARALLEL, FORWARD, BACKWARD, computation, interval
from .utils import *
from . import *
from shalconv.funcphys import fpvsx_gt as fpvs
from shalconv.physcons import (
    con_g     as g,
    con_cp    as cp,
    con_hvap  as hvap,
    con_rv    as rv,
    con_fvirt as fv,
    con_t0c   as t0c,
    con_rd    as rd,
    con_cvap  as cvap,
    con_cliq  as cliq,
    con_eps   as eps,
    con_epsm1 as epsm1,
    con_e     as e
)

@gtscript.stencil(backend=BACKEND, rebuild=REBUILD)
def pa_to_cb( psp  : FIELD_FLOAT, 
              prslp: FIELD_FLOAT,
              delp : FIELD_FLOAT,
              ps   : FIELD_FLOAT,
              prsl : FIELD_FLOAT,
              del0  : FIELD_FLOAT ):

    with computation(PARALLEL), interval(...):
        
        # Convert input Pa terms to Cb terms
        ps   = psp   * 0.001
        prsl = prslp * 0.001
        del0  = delp  * 0.001
        

@gtscript.stencil(backend=BACKEND, rebuild=REBUILD)
def init_col_arr( km    : DTYPE_INT,
                  kcnv  : FIELD_INT, 
                  cnvflg: FIELD_INT,
                  kbot  : FIELD_INT,
                  ktop  : FIELD_INT,
                  kbcon : FIELD_INT,
                  kb    : FIELD_INT,
                  rn    : FIELD_FLOAT,
                  gdx   : FIELD_FLOAT,
                  garea : FIELD_FLOAT ):
    
    with computation(PARALLEL), interval(...):
        
        # Initialize column-integrated and other single-value-per-column 
        # variable arrays
        if (kcnv == 1):
            cnvflg = 0
            
        if (cnvflg == 1):
            kbot = km + 1
            ktop = 0
            
        rn    = 0.0
        kbcon = km
        kb    = km
        gdx   = sqrt(garea)


@gtscript.stencil(backend=BACKEND, rebuild=REBUILD)
def init_par_and_arr( c0s    : DTYPE_FLOAT,
                      asolfac: DTYPE_FLOAT,
                      d0     : DTYPE_FLOAT,
                      islimsk: FIELD_INT,
                      c0     : FIELD_FLOAT,
                      t1     : FIELD_FLOAT,
                      c0t    : FIELD_FLOAT,
                      cnvw   : FIELD_FLOAT,
                      cnvc   : FIELD_FLOAT,
                      ud_mf  : FIELD_FLOAT,
                      dt_mf  : FIELD_FLOAT ):
    
    with computation(PARALLEL), interval(...):
        
        # Determine aerosol-aware rain conversion parameter over land
        if islimsk == 1:
            c0 = c0s * asolfac
        else:
            c0 = c0s
            
        # Determine rain conversion parameter above the freezing level 
        # which exponentially decreases with decreasing temperature 
        # from Han et al.'s (2017) \cite han_et_al_2017 equation 8
        tem = exp(d0 * (t1 - 273.16)) 
        if t1 > 273.16:
            c0t = c0
        else:
            c0t = c0 * tem
            
        # Initialize convective cloud water and cloud cover to zero
        cnvw = 0.0
        cnvc = 0.0
        
        # Initialize updraft mass fluxes to zero
        ud_mf = 0.0
        dt_mf = 0.0


@gtscript.stencil(backend=BACKEND, rebuild=REBUILD, externals={"min": min, "max": max, "fpvs": fpvs})
def init_final( km    : DTYPE_INT,
                kbm   : FIELD_INT,
                k_idx : FIELD_INT,
                kmax  : FIELD_INT,
                flg   : FIELD_INT,
                cnvflg: FIELD_INT,
                kpbl  : FIELD_INT,
                tx1   : FIELD_FLOAT,
                ps    : FIELD_FLOAT,
                prsl  : FIELD_FLOAT,
                zo    : FIELD_FLOAT,
                phil  : FIELD_FLOAT,
                zi    : FIELD_FLOAT,
                pfld  : FIELD_FLOAT,
                eta   : FIELD_FLOAT,
                hcko  : FIELD_FLOAT,
                qcko  : FIELD_FLOAT,
                qrcko : FIELD_FLOAT,
                ucko  : FIELD_FLOAT,
                vcko  : FIELD_FLOAT,
                dbyo  : FIELD_FLOAT,
                pwo   : FIELD_FLOAT,
                dellal: FIELD_FLOAT,
                to    : FIELD_FLOAT,
                qo    : FIELD_FLOAT,
                uo    : FIELD_FLOAT,
                vo    : FIELD_FLOAT,
                wu2   : FIELD_FLOAT,
                buo   : FIELD_FLOAT,
                drag  : FIELD_FLOAT,
                cnvwt : FIELD_FLOAT,
                qeso  : FIELD_FLOAT,
                heo   : FIELD_FLOAT,
                heso  : FIELD_FLOAT,
                hpbl  : FIELD_FLOAT,
                t1    : FIELD_FLOAT,
                q1    : FIELD_FLOAT,
                u1    : FIELD_FLOAT,
                v1    : FIELD_FLOAT ):
    
    from __externals__ import min, max, fpvs
    
    with computation(PARALLEL), interval(...):
        
        # Determine maximum indices for the parcel starting point (kbm) 
        # and cloud top (kmax)
        kbm  = km
        kmax = km
        tx1  = 1.0/ps
        
        if prsl * tx1 > 0.7: kbm  = k_idx + 1
        if prsl * tx1 > 0.6: kmax = k_idx + 1
        
        kbm = min(kbm, kmax)
        
        # Calculate hydrostatic height at layer centers assuming a flat 
        # surface (no terrain) from the geopotential
        zo = phil/g
        
        # Initialize flg in parallel computation block
        flg = cnvflg

        kpbl = 1
        
    with computation(PARALLEL), interval(0, -1):
        
        # Calculate interface height
        zi = 0.5 * (zo[0, 0, 0] + zo[0, 0, +1])
    
    with computation(FORWARD),interval(1,-1):
        
        # Find the index for the PBL top using the PBL height; enforce 
        # that it is lower than the maximum parcel starting level
        if flg[0, 0, -1] and (zo <= hpbl):
            kpbl = k_idx
            flg  = flg[0, 0, -1]
        else:
            kpbl = kpbl[0, 0, -1]
            flg  = 0#False
    
    with computation(BACKWARD),interval(0,-1):
        
        # Propagate results back to update whole field
        kpbl = kpbl[0, 0, 1]
        flg  = flg[0, 0, 1]
    
    with computation(PARALLEL), interval(...):
        
        kpbl = min(kpbl, kbm)

        # Calculate saturation specific humidity and enforce minimum 
        # moisture values
        pfld = prsl * 10.0
        qo   = q1
        qeso = (0.01 * eps * fpvs(to))/(pfld + epsm1 * qeso)    # fpsv is a function (can't be called inside conditional), also how to access lookup table?
        val1 = 1.0e-8
        val2 = 1.0e-10
        qeso = max(qeso, val1 )
        qo   = max(qo  , val2)

        #temporary var have to be defined outside of if-clause
        tem  = 0.0
        
        if cnvflg == 1 and k_idx <= kmax:
            
            # Convert prsl from centibar to millibar, set normalized mass 
            # flux to 1, cloud properties to 0, and save model state 
            # variables (after advection/turbulence)
            pfld   = prsl * 10.0
            eta    = 1.0
            hcko   = 0.0
            qcko   = 0.0
            qrcko  = 0.0
            ucko   = 0.0
            vcko   = 0.0
            dbyo   = 0.0
            pwo    = 0.0
            dellal = 0.0
            to     = t1
            qo     = q1
            uo     = u1
            vo     = v1
            wu2    = 0.0
            buo    = 0.0
            drag   = 0.0
            cnvwt  = 0.0
            
            # Calculate saturation specific humidity and enforce minimum 
            # moisture values
            #qeso = (0.01 * eps * fpvs(to))/(pfld + epsm1 * qeso)    # fpsv is a function (can't be called inside conditional), also how to access lookup table?
            #val1 = 1.0e-8
            #val2 = 1.0e-10
            #qeso = max(qeso, val1 )
            #qo   = max(qo  , val2)
            
            # Calculate moist static energy (heo) and saturation moist 
            # static energy (heso)
            tem  = phil + cp * to
            heo  = tem + hvap * qo
            heso = tem + hvap * qeso   
    

@gtscript.stencil(backend=BACKEND, rebuild=REBUILD)
def init_tracers( cnvflg: FIELD_INT,
                  k_idx : FIELD_INT,
                  kmax  : FIELD_INT,
                  ctr   : FIELD_FLOAT, 
                  ctro  : FIELD_FLOAT, 
                  ecko  : FIELD_FLOAT,
                  qtr   : FIELD_FLOAT ):
    
    with computation(PARALLEL), interval(...):
        
        # Initialize tracer variables
        if cnvflg == 1 and k_idx <= kmax:
            ctr  = qtr
            ctro = qtr
            ecko = 0.0