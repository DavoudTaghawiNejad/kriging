

from __future__ import division
from kriging import Kriging
import os
from pprint import pprint
from math import ceil


def scale(number):
    return ceil(number / 1000)

gdp_2011 = 669506666667                         # Worldbank databank.worldbank.org/data/saudiGDP/id/3e2250a0
gdp_2012 = 711049600000

target = {
    'before_policy': {                  # 2011
                                        #'distributed_profits': None,
                                        #'net_worth': None,
                                        'num_saudis': scale(645716),            # Nitaqat Data 7/9/11
                                        'num_expats': scale(6767411),           # "
                                        'num_firms': scale(1154093),            # " count of unique indexes
                                        #'planned_production': None,
                                        'price': 1,
                                        'production': gdp_2011,
                                        #'profit': None,
                                        'wage_saudis': 5349.40,                 # MOL Average Wages by Economic Activity, Gender and Nationality (2010-2012) file://
                                        'wage_expats': 948.26,                  # ""
    },

    'after_policy': {                   # 2012
                                        #'distributed_profits': None,
                                        #'net_worth': None,
                                        'num_saudis': scale(1066694),           # Nitaqat Data 10/13/12 (use 12/7/13 for verification)
                                        'num_expats': scale(6708712),           # "
                                        'num_firms': scale(1252599),            # " count of unique indexes
                                        #'planned_production': None,
                                        'price': 1.035,                         # compared to previous year Worldbank http://data.worldbank.org/indicator/FP.CPI.TOTL.ZG
                                        'production': gdp_2011,
                                        #'profit': None,
                                        'wage_saudis': 4801.42,                 # MOL Average Wages by Economic Activity, Gender and Nationality (2010-2012) file://
                                        'wage_expats': 940.15,                  # ""
    },
    }

#pylint: disable=W0511

parameters = {
    'assumptions':
        {
            'setup_period_1': 5,                  # random.randint(1,5)750,
            'setup_period_2': 5,
            'time_before_policy': 5,
            'time_after_policy': 5,
            'num_saudis': scale(16107264),          # total population in working age 19 - 60, 2-A Labor Force Survey 2011
            'minimum_mark_up': 1.1,
            'initial_net_worth_mean': 10000,
            'initial_net_worth_std': 2000,
            'days_pay_must_be_available': 30,
            'percent_distribute_pyear': 0.9,        # correct? #TODO
            'production_function_exponent': 1,
            'initial_wage_offer_saudi_pmonth': 5000,
            'initial_wage_offer_expat_pmonth': 900,
            'reapplication_probability_expat': 0.0,
            'num_of_advertisment_pmonth': 4,
            },
    'before_policy':
        {
            'expat_minimum_wage_pmonth': 0.0,
            'expat_tax_per_head_pmonth': 0.0,
            'expat_tax_percentage': 0.0,
            'saudi_minimum_wage_pmonth': 0.0,
            'saudi_tax_per_head_pmonth': 0.0,
            'saudi_tax_percentage': 0.0,
            'sauditization_percentage': 0.0,
            'visa_length': 356
        },
    'after_policy':
        {
            'expat_minimum_wage_pmonth': 0.0,
            'expat_tax_per_head_pmonth': 0.0,
            'expat_tax_percentage': 0.0,
            'saudi_minimum_wage_pmonth': 0.0,
            'saudi_tax_per_head_pmonth': 0.0,
            'saudi_tax_percentage': 0.0,
            'sauditization_percentage': 0.15,
            'visa_length': 356
        }
}

lower_limits = {
    'assumptions': {
        'love_for_variety': 0.01,
        'num_expats': scale(17259700),
        'num_firms': scale(1154093),
        'productivity_mean_saudi_pyear': 500.0,
        'productivity_mean_expat_pyear': 500.0,
        'productivity_std_saudi_pyear': 0.0,
        'productivity_std_expat_pyear': 0.0,
        'reapplication_probability_saudi': 0.0,
        'reservation_wage_mean_saudi': 1000.0,
        'reservation_wage_std_saudi': 500.0,
        'reservation_wage_mean_expat': 200.0,
        'reservation_wage_std_expat': 0.0,
        'sector_spending_pyear': scale(gdp_2011 / 4),
        'price_step_increase_pyear': 1,
        'price_step_decrease_pyear': 1,
        'wage_step_saudi_pyear': 1,
        'wage_step_expat_pyear': 1,
        'planned_production_step_increase_pyear': 3,
        'planned_production_step_decrease_pyear': 3,
        'required_roi_pyear': 0.07,

        }
}

upper_limits = {
    'assumptions': {
        'love_for_variety': 0.90,
        'num_expats': scale(20000000),
        'num_firms': scale(1200000),
        'productivity_mean_saudi_pyear': gdp_2011 / target['before_policy']['num_saudis'],
        'productivity_mean_expat_pyear': gdp_2011 / target['before_policy']['num_expats'],
        'productivity_std_saudi_pyear': gdp_2011 / target['before_policy']['num_saudis'] / 10,
        'productivity_std_expat_pyear': gdp_2011 / target['before_policy']['num_expats'] / 10,
        'reapplication_probability_saudi': .05,
        'reservation_wage_mean_saudi': 4000.0,
        'reservation_wage_std_saudi': 1000.0,
        'reservation_wage_mean_expat': 400.0,
        'reservation_wage_std_expat': 1000.0,
        'sector_spending_pyear': scale(gdp_2011 * 2),
        'price_step_increase_pyear': 2,
        'price_step_decrease_pyear': 2,
        'wage_step_saudi_pyear': 2,
        'wage_step_expat_pyear': 2,
        'planned_production_step_increase_pyear': 30,
        'planned_production_step_decrease_pyear': 30,
        'required_roi_pyear': 0.30,
        }
}

dtypes = {
    'assumptions': {
        'love_for_variety': float,
        'num_expats': int,
        'num_firms': int,
        'productivity_mean_saudi_pyear': float,
        'productivity_mean_expat_pyear': float,
        'productivity_std_saudi_pyear': float,
        'productivity_std_expat_pyear': float,
        'reapplication_probability_saudi': float,
        'reservation_wage_mean_saudi': float,
        'reservation_wage_std_saudi': float,
        'reservation_wage_mean_expat': float,
        'reservation_wage_std_expat': float,
        'sector_spending_pyear': float,
        'price_step_increase_pyear': float,
        'price_step_decrease_pyear': float,
        'wage_step_saudi_pyear': float,
        'wage_step_expat_pyear': float,
        'planned_production_step_increase_pyear': float,
        'planned_production_step_decrease_pyear': float,
        'required_roi_pyear': float,
        }
}

sweep_intervals = {
    'assumptions': {
        'love_for_variety': 5,
        'num_expats': 5,
        'num_firms': 3,
        'productivity_mean_saudi_pyear': 3,
        'productivity_mean_expat_pyear': 3,
        'productivity_std_saudi_pyear': 2,
        'productivity_std_expat_pyear': 2,
        'reapplication_probability_saudi': 2,
        'reservation_wage_mean_saudi': 3,
        'reservation_wage_std_saudi': 2,
        'reservation_wage_mean_expat': 3,
        'reservation_wage_std_expat': 2,
        'sector_spending_pyear': 4,
        'price_step_increase_pyear': 3,
        'price_step_decrease_pyear': 3,
        'wage_step_saudi_pyear': 3,
        'wage_step_expat_pyear': 3,
        'planned_production_step_increase_pyear': 3,
        'planned_production_step_decrease_pyear': 3,
        'required_roi_pyear': 3,
        }
}


def calibration():
    calibration = Kriging(
        db_name='test',
        target=target,
        fixed_parameters=parameters,
        lower_limits=lower_limits,
        upper_limits=upper_limits,
        initial_runs=22,
        dtypes=dtypes,
        repetitions=7
    )

    outcome, stats = calibration.kriging(batch_size=22, success=0.01, sweep_intervals=sweep_intervals)
    pprint(stats)
    return calibration

if __name__ == '__main__':
    os.system('clear')  # on linux / os x
    #self = calibration
    self = calibration()
