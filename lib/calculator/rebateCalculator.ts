import bcPrograms from '@/data/programs/bc.json';

export interface CalculatorInputs {
  province: 'bc' | 'on';
  city: string;
  utility: 'bc_hydro' | 'fortisbc';
  own_rent: 'own' | 'rent';
  home_type: 'detached' | 'townhome' | 'condo' | 'apartment';
  heating_fuel: 'gas' | 'electric_baseboard' | 'oil' | 'propane' | 'heat_pump' | 'unsure';
  built_year: 'pre_1980' | '1980_2000' | '2000_plus' | 'unsure';
  household_size: number;
  household_income: 'level_1' | 'level_2' | 'level_3' | 'prefer_not_say';
  selected_upgrades: string[]; // 'insulation', 'heat_pump', 'solar', 'battery', etc.
}

export interface RebateResult {
  upgrade: string;
  label: string;
  rebate_amount_low: number;
  rebate_amount_high: number;
  rebate_amount: number | null;
  typical_net_cost: number | null;
  estimated_monthly_savings: number | null;
  order: number;
  available: boolean;
  reason_if_unavailable: string | null;
  conditions: string[];
  source: string;
  verified_date: string;
}

export interface CalculatorResults {
  city: string;
  province: string;
  utility: string;
  household_size: number;
  income_level: string;
  home_type: string;
  heating_fuel: string;
  is_renter: boolean;
  is_condo: boolean;
  total_rebates_low: number;
  total_rebates_high: number;
  total_rebates: number;
  estimated_net_cost_total: number | null;
  estimated_monthly_bill_impact: number | null;
  upgrades: RebateResult[];
  free_offerings: string[];
  next_actions: string[];
}

// Income tier lookup
const getIncomeTier = (size: string, income: string): string | null => {
  const tierKey = size === '7_plus' ? '7_plus' : size;
  const tiers = bcPrograms.income_tiers.tiers[tierKey];

  if (!tiers) return null;

  if (income === 'level_1') {
    return income;
  } else if (income === 'level_2') {
    return income;
  } else if (income === 'level_3') {
    return income;
  }
  return 'level_1'; // default
};

// Get heat pump rebate based on income tier
const getHeatPumpRebate = (
  utility: 'bc_hydro' | 'fortisbc',
  income_level: string,
  home_type: string
): number => {
  if (utility === 'bc_hydro') {
    if (home_type === 'condo' || home_type === 'apartment') {
      // Condo/apartment electrically heated: $5K flat
      return 5000;
    }
    // Ground-oriented homes by income
    const rebates = bcPrograms.programs.heat_pump_esp.bc_hydro.rebate_by_income;
    return rebates[income_level] || rebates.level_1;
  } else if (utility === 'fortisbc') {
    // FortisBC: flat $4K for whole home, $1.5K for partial
    return 4000; // assume whole-home for now
  }
  return 0;
};

// Main calculator function
export const calculateRebates = (inputs: CalculatorInputs): CalculatorResults => {
  const { province, city, utility, own_rent, home_type, heating_fuel, built_year, household_size, household_income, selected_upgrades } = inputs;

  const is_renter = own_rent === 'rent';
  const is_condo = home_type === 'condo' || home_type === 'apartment';
  const income_tier = getIncomeTier(household_size.toString(), household_income);

  const upgrades: RebateResult[] = [];
  let total_rebates = 0;
  const free_offerings: string[] = [];

  // INSULATION & AIR SEALING
  if (selected_upgrades.includes('insulation')) {
    upgrades.push({
      upgrade: 'insulation',
      label: 'Insulation & air sealing',
      rebate_amount_low: 1000,
      rebate_amount_high: 5000,
      rebate_amount: 3000, // typical
      typical_net_cost: 8000,
      estimated_monthly_savings: 15,
      order: 1,
      available: !is_renter,
      reason_if_unavailable: is_renter ? 'Renters need landlord consent' : null,
      conditions: [
        'Improves thermal envelope',
        'Reduces air leakage',
        'Part of Energy Savings Program application'
      ],
      source: 'BetterHomesBC / BC Hydro',
      verified_date: '2026-07-12'
    });
  }

  // HEAT PUMP
  if (selected_upgrades.includes('heat_pump')) {
    const hp_rebate = getHeatPumpRebate(utility, income_tier, home_type);
    const hp_net_cost = 12000; // typical installed cost after rebate

    upgrades.push({
      upgrade: 'heat_pump',
      label: 'Air source heat pump',
      rebate_amount_low: hp_rebate * 0.8,
      rebate_amount_high: hp_rebate * 1.2,
      rebate_amount: hp_rebate,
      typical_net_cost: hp_net_cost,
      estimated_monthly_savings: 140,
      order: 2,
      available: !is_renter || true, // renters can apply with consent
      reason_if_unavailable: null,
      conditions: [
        heating_fuel === 'gas' ? 'Replaces gas furnace' : 'Replaces electric resistance heating',
        'HPCN-certified contractor',
        'Cold-climate model on NRCan list',
        built_year === 'pre_1980' ? 'May require electrical panel upgrade' : 'No panel upgrade likely needed'
      ],
      source: utility === 'bc_hydro' ? 'BetterHomesBC' : 'FortisBC',
      verified_date: '2026-07-12'
    });

    total_rebates += hp_rebate;
  }

  // SOLAR
  if (selected_upgrades.includes('solar')) {
    upgrades.push({
      upgrade: 'solar',
      label: 'Solar PV system',
      rebate_amount_low: 4000,
      rebate_amount_high: 5000,
      rebate_amount: 5000,
      typical_net_cost: 15000,
      estimated_monthly_savings: 120,
      order: 3,
      available: !is_condo && !is_renter,
      reason_if_unavailable: is_condo ? 'Condo/apartment units not eligible' : is_renter ? 'Renters not eligible' : null,
      conditions: [
        'HPCN-certified contractor required since June 1, 2026',
        'Pre-approval BEFORE purchasing equipment',
        'Size to self-consumption (not export)',
        'Excess exported at 10¢/kWh (new self-generation rate, July 1, 2026)'
      ],
      source: 'BC Hydro',
      verified_date: '2026-07-12'
    });

    total_rebates += 5000;
  }

  // BATTERY
  if (selected_upgrades.includes('battery')) {
    upgrades.push({
      upgrade: 'battery',
      label: 'Battery energy storage',
      rebate_amount_low: 1500,
      rebate_amount_high: 5000,
      rebate_amount: 5000, // if Peak Saver enrolled within 14 days
      typical_net_cost: 10000,
      estimated_monthly_savings: 80,
      order: 4,
      available: !is_condo && !is_renter,
      reason_if_unavailable: is_condo ? 'Condo/apartment units not eligible' : is_renter ? 'Renters not eligible' : null,
      conditions: [
        'Minimum 5 kWh capacity',
        'Must enroll in Peak Saver within 14 days of approval',
        'If not enrolled: $1,500 max (lose $3,500)',
        'Pairs with solar: store midday excess for evening peak use'
      ],
      source: 'BC Hydro',
      verified_date: '2026-07-12'
    });

    total_rebates += 5000;
  }

  // FREE SMART THERMOSTATS (if baseboard heat)
  if (heating_fuel === 'electric_baseboard') {
    free_offerings.push('Free smart thermostats (5 units, ~$350 value, October 2026)');
  }

  // FREE ENERGY SAVING KIT (if income-qualified)
  if (household_income === 'level_1' || household_income === 'level_2') {
    free_offerings.push('Free energy saving kit (LED bulbs, weather stripping, showerheads, etc.)');
  }

  // FREE RETROFIT PROGRAM (if income-qualified)
  if (household_income === 'level_1') {
    free_offerings.push('Free home energy retrofit (ECAP) — heat pump + insulation installation, income-qualified');
  }

  // Next actions
  const next_actions: string[] = [
    'Register for free smart thermostats (ships October 2026)',
    'Run Energy Savings Program pre-qualification at https://bcenergysavingsprogram.ca',
    'Get 2–3 quotes from HPCN-certified contractors'
  ];

  return {
    city,
    province,
    utility,
    household_size,
    income_level: income_tier || 'standard',
    home_type,
    heating_fuel,
    is_renter,
    is_condo,
    total_rebates_low: total_rebates * 0.85,
    total_rebates_high: total_rebates * 1.15,
    total_rebates,
    estimated_net_cost_total: 35000, // typical
    estimated_monthly_bill_impact: -180, // negative = savings
    upgrades: upgrades.filter(u => u.available),
    free_offerings,
    next_actions
  };
};

// URL encoding/decoding for shareable links
export const encodeCalculatorUrl = (inputs: Partial<CalculatorInputs>): string => {
  const params = new URLSearchParams();

  if (inputs.city) params.set('city', inputs.city);
  if (inputs.own_rent) params.set('own', inputs.own_rent === 'own' ? '1' : '0');
  if (inputs.home_type) params.set('ht', inputs.home_type);
  if (inputs.heating_fuel) params.set('heat', inputs.heating_fuel);
  if (inputs.built_year) params.set('yr', inputs.built_year);
  if (inputs.household_size) params.set('size', inputs.household_size.toString());
  if (inputs.household_income) params.set('inc', inputs.household_income);
  if (inputs.selected_upgrades && inputs.selected_upgrades.length > 0) {
    params.set('sel', inputs.selected_upgrades.join(','));
  }

  return params.toString();
};

export const decodeCalculatorUrl = (queryString: string): Partial<CalculatorInputs> => {
  const params = new URLSearchParams(queryString);

  return {
    city: params.get('city') || undefined,
    own_rent: params.get('own') === '1' ? 'own' : 'rent',
    home_type: (params.get('ht') as any) || undefined,
    heating_fuel: (params.get('heat') as any) || undefined,
    built_year: (params.get('yr') as any) || undefined,
    household_size: params.get('size') ? parseInt(params.get('size')!) : undefined,
    household_income: (params.get('inc') as any) || undefined,
    selected_upgrades: params.get('sel')?.split(',') || []
  };
};
