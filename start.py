""" This is an example start.py file that starts the kriging mechanism

"""
from __future__ import division
from kriging import Kriging
from pprint import pprint
import json
import inspect

parameters = {
    "control": {
        "timeout": 30
    },
    "assumptions": {
        "demand_multiplier": (1, 50, float),
        "fixed_cost_pyear": (0, 100000, float),
        "initial_wage_offer_expat_pmonth": (300.0, 1000.0, float),
        "initial_wage_offer_saudi_pmonth": (300, 4047.107524383257, float),

        "love_for_variety": (0.1, 0.9, float),
        "minimum_mark_up": (1.01, 1.10, float),

        "num_expats": (400, 600, int),
        "num_saudis": (50, 100, int),

        "percent_distribute_pyear": (0.001, 0.999, float),

        "setup_period_1": 750,
        "setup_period_2": 750,
        "time_after_policy": 2000,
        "time_before_policy": 0,
        "num_firms": 30,

        "planned_production_step_decrease_pyear": (1.1, 20, float),
        "planned_production_step_increase_pyear": (1.1, 20, float),
        "price_step_decrease_pyear": (1.01, 4.0, float),
        "price_step_increase_pyear": (1.01, 4.0, float),

        "productivity_mean_expat_pmonth": (300.0, 20000, float),   #!
        "productivity_mean_saudi_pmonth": (300.0, 20000, float),
        "productivity_std_expat_pmonth": (0, 3000, float),
        "productivity_std_saudi_pmonth": (0, 3000, float),

        "required_roi_pyear": (0.001, 0.80, float),

        "reservation_wage_mean_expat": (300.0, 1000.0, float),
        "reservation_wage_mean_saudi": (300, 4047.107524383257, float),
        "reservation_wage_std_expat": (0, 1000, float),
        "reservation_wage_std_saudi": (0, 2000, float),

        "sector_spending_pmonth": (5004077899 / 10, 954318338610.0 / 2, float),

        "wage_step_expat_pyear": (1.01, 4, float),
        "wage_step_saudi_pyear": (1.01, 4, float),

        "reapplication_probability_saudi": 0.01076245503283952,
        "reapplication_probability_expat": 0.0,

        "initial_net_worth_mean": 1000,
        "initial_net_worth_std": 100,
        "days_pay_must_be_available": 30,
        "production_function_exponent": 1,
        "time_idle": (30, 90, int)
    },
    "before_policy": {
        "saudi_minimum_wage_pmonth": 0,
        "expat_minimum_wage_pmonth": 0,
        "saudi_tax_percentage": 0,
        "expat_tax_percentage": 0,
        "saudi_tax_per_head_pmonth": 0,
        "expat_tax_per_head_pmonth": 0,
        "visa_length": 30,
        "quota1": 0.0,
        "quota2": 0.0,
        "quota3": 0.0,
        "quota4": 0.0,
        "quota5": 0.0,
    },
    "after_policy": {
        "saudi_minimum_wage_pmonth": 0,
        "expat_minimum_wage_pmonth": 0,
        "saudi_tax_percentage": 0,
        "expat_tax_percentage": 0,
        "saudi_tax_per_head_pmonth": 0,
        "expat_tax_per_head_pmonth": 0,
        "visa_length": 30,
        "quota1": 0.0,
        "quota2": 0.14,
        "quota3": 0.24,
        "quota4": 0.29,
        "quota5": 0.29,
    },
}
# Industry  ID Number of Firms Saudi Employees Expatriate Employees    Total Employees     Number of Firms Saudi Employees Expatriate Employees    Total Employees
# Manufacturing 6   6981       69096           348929                  418025              6984            96201           335150                  431351
target = {
    'after_policy': {
        'num_expats': 25,
        'num_saudis': 10,


    },
    "before_policy": {
        'num_expats': 30,
        'num_saudis': 5,

    },
    'ratio': {
#        'saudis': 4356 / 4584,  # 0.95
#        'expats': 7243 / 15709,  # 0.46
#        'saudis_expats': 4356 / 7243,  # 0.60
#        'firms': 63 / 83,  #  0.75
         #'inflation': 1.089 ** 2
    }
}



def transform(self, x):
    x['ratio'] = {}
    x['ratio']['inflation'] = (x["after_policy"]['price'] - x["before_policy"]['price']) / x["before_policy"]['price']
#    try:
#        x['ratio']['saudis'] = x['after_policy']['num_saudis'] / x['before_policy']['num_saudis']
#    except ZeroDivisionError:
#        x['ratio']['saudis'] = 0
#    try:
#        x['ratio']['expats'] = x['after_policy']['num_expats'] / x['before_policy']['num_expats']
#    except ZeroDivisionError:
#        x['ratio']['expats'] = 0
#    try:
#        x['ratio']['saudis_expats'] = x['after_policy']['num_saudis'] / x['after_policy']['num_expats']
#    except ZeroDivisionError:
#        x['ratio']['saudis_expats'] = 0
#    try:
#        x['ratio']['firms'] = x['after_policy']['num_firms'] / x['before_policy']['num_firms']
#    except ZeroDivisionError:
#        x['ratio']['firms'] = 0
    return x

def calibration():
    # the kriging algorithem gets a targets, to which the sum of squares should be
    # minimized
    calibration = Kriging(
        target=target,
        parameters=parameters,
        db_name=inspect.getfile(inspect.currentframe()),
        repetitions=6,
        transform=transform
        )
    calibration.initialize(44)
    input, output =  calibration.kriging(batch_size=44, success=0.05, schlinge_start=2.0, schlinge_change=0.025, kriging_on=False)
    print("************* INPUT ************************** INPUT ************************** INPUT *************")
    print(json.dumps(input, 20))
    print("************ OUTPUT ************************** OUTPUT ************************** OUTPUT ************")
    print(json.dumps(output, 20))
    #calibration.run_input(0.5)
    return calibration

if __name__ == '__main__':
    import os


    os.system('clear')  # on linux / os x
    #self = calibration
    self = calibration()
