# -*- coding: utf-8 -*-
"""
Created on Sun May 26 19:31:51 2024

@author: jvilp
"""

from enum import Enum, auto

class Rebalancing_frequency(Enum):
    
    MONTHLY = auto()
    QUARTERLY = auto()
    YEARLY = auto()
    
    
class Transaction_cost(Enum):
    
    NULL = auto()
    CONSTANT = auto()
    LINEAR = auto()
    AFFINE = auto()
    
    
class Strategy(Enum):
    
    EQUAL_WEIGHTED = auto()
    MOMENTUM = auto()
    REVERSAL = auto()
    CO_MOM_REV = auto()
    