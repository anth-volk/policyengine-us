from openfisca_core.model_api import *
from openfisca_us.entities import *
from openfisca_us.tools.general import *


class snap_earnings_deduction(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = YEAR
    documentation = ""

    def formula(spm_unit, period, parameters):

        snap_earnings_deduction = parameters(
            period
        ).benefits.snap.earnings_deduction

        return spm_unit("gross_income", period) * snap_earnings_deduction


class snap_standard_deduction(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = YEAR
    documentation = ""

    def formula(spm_unit, period, parameters):

        standard_deductions = parameters(
            period
        ).benefits.snap.standard_deduction

        state_group = spm_unit("state_group")

        household_size = spm_unit("household_size")

        return standard_deductions[state_group][household_size] * 12


class snap_net_income_pre_shelter(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = YEAR
    documentation = ""

    def formula(spm_unit, period, parameters):

        return (
            spm_unit("gross_income", period)
            - spm_unit("snap_standard_deduction", period)
            - spm_unit("snap_earnings_deduction", period)
        )


class snap_shelter_deduction(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = YEAR
    documentation = ""

    def formula(spm_unit, period, parameters):
        # TODO: MUltiply params by 12.
        # check for member of spm_unit with disability/elderly status
        p_shelter_deduction = parameters(
            period
        ).benefits.snap.shelter_deduction

        # Calculate uncapped shelter deduction as housing costs in excess of
        # income threshold
        uncapped_ded = max_(
            spm_unit("housing_cost", period)
            - (
                p_shelter_deduction.income_share_threshold
                * spm_unit("snap_net_income_pre_shelter", period)
            ),
            0,
        )

        # Index maximum shelter deduction by state group.
        state_group = spm_unit("state_group", period)
        ded_cap = p_shelter_deduction.amount[state_group]

        has_elderly_disabled = spm_unit("has_elderly_disabled", period)
        # Cap for all but elderly/disabled people.
        return where(
            has_elderly_disabled, uncapped_ded, min_(uncapped_ded, ded_cap)
        )


class snap_net_income(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = YEAR
    documentation = ""

    def formula(spm_unit, period, parameters):

        return spm_unit("snap_net_income_pre_shelter", period) - spm_unit(
            "snap_shelter_deduction", period
        )


class snap_expected_contribution_towards_food(Variable):

    value_type = float
    entity = SPMUnit
    definition_period = YEAR
    documentation = ""

    def formula(spm_unit, period, parameters):
        # TODO: Use the parameter

        expected_food_contribution = parameters(
            period
        ).benefit.snap.expected_food_contribution
        return spm_unit("snap_net_income", period) * expected_food_contribution


class snap_max_benefit(Variable):

    value_type = float
    entity = SPMUnit
    definition_period = YEAR
    documentation = ""

    def formula(spm_unit, period, parameters):

        # TODO: Logic for families with >8 people
        snap_max_benefits = parameters(period).benefits.snap.amount.main

        state_group = spm_unit("spm_unit_state_group", period)
        # TODO: Use number_persons
        household_size = spm_unit.nb_persons()

        return snap_max_benefits[household_size][state_group] * 12


class snap(Variable):

    value_type = float
    entity = SPMUnit
    definition_period = YEAR
    documentation = ""

    def formula(spm_unit, period, parameters):
        # TODO: Add gross and net income checks.
        return spm_unit("snap_max_benefit", period) - spm_unit(
            "snap_expected_contribution_towards_food", period
        )