'use client';

import { useState, useEffect } from 'react';
import { CalculatorInputs, calculateRebates, encodeCalculatorUrl } from '@/lib/calculator/rebateCalculator';
import CalculatorResults from './CalculatorResults';

const CITIES = [
  'Kelowna', 'Vancouver', 'Victoria', 'Calgary', 'Edmonton',
  'Surrey', 'Burnaby', 'Richmond', 'Coquitlam', 'Maple Ridge',
  'Abbotsford', 'Nanaimo', 'Kamloops', 'Prince George'
];

const HOME_TYPES = [
  { value: 'detached', label: 'Detached house' },
  { value: 'townhome', label: 'Townhome or row house' },
  { value: 'condo', label: 'Condo or apartment' }
];

const HEATING_FUELS = [
  { value: 'gas', label: 'Gas furnace' },
  { value: 'electric_baseboard', label: 'Electric baseboard' },
  { value: 'oil', label: 'Oil or propane' },
  { value: 'heat_pump', label: 'Heat pump (already have)' },
  { value: 'unsure', label: 'Not sure' }
];

const BUILT_YEARS = [
  { value: 'pre_1980', label: 'Before 1980' },
  { value: '1980_2000', label: '1980–2000' },
  { value: '2000_plus', label: '2000 or later' },
  { value: 'unsure', label: 'Not sure' }
];

const HOUSEHOLD_SIZES = [1, 2, 3, 4, 5, 6, 7];

interface CalculatorStepperProps {
  initialCity?: string;
  embedded?: boolean; // For homepage compact mode
}

export default function CalculatorStepper({ initialCity, embedded = false }: CalculatorStepperProps) {
  const [step, setStep] = useState<number>(0); // 0 = city, 1 = own/rent, etc.
  const [inputs, setInputs] = useState<Partial<CalculatorInputs>>({
    province: 'bc',
    city: initialCity || '',
    utility: 'bc_hydro',
    own_rent: undefined,
    home_type: undefined,
    heating_fuel: undefined,
    built_year: undefined,
    household_size: undefined,
    household_income: undefined,
    selected_upgrades: ['insulation', 'heat_pump', 'solar', 'battery'] // Default to all
  });
  const [showResults, setShowResults] = useState(false);
  const [results, setResults] = useState(null);

  const questions = [
    {
      key: 'city',
      title: 'Where are you located?',
      type: 'select',
      options: CITIES,
      skip: !!initialCity
    },
    {
      key: 'own_rent',
      title: 'Do you own your home?',
      type: 'choice',
      options: [
        { value: 'own', label: 'I own it' },
        { value: 'rent', label: 'I rent it' }
      ]
    },
    {
      key: 'home_type',
      title: 'What type of home?',
      type: 'choice',
      options: HOME_TYPES
    },
    {
      key: 'heating_fuel',
      title: 'How do you heat your home?',
      type: 'choice',
      options: HEATING_FUELS
    },
    {
      key: 'built_year',
      title: 'Roughly when was it built?',
      type: 'choice',
      options: BUILT_YEARS
    },
    {
      key: 'household_size',
      title: 'How many people live there?',
      type: 'number',
      options: HOUSEHOLD_SIZES
    },
    {
      key: 'household_income',
      title: 'Household income (optional)',
      type: 'choice',
      options: [
        { value: 'prefer_not_say', label: 'Prefer not to say' },
        { value: 'level_1', label: 'Below $' + 51100 },
        { value: 'level_2', label: '$51K – $135K' },
        { value: 'level_3', label: 'Above $135K' }
      ],
      hint: 'Lower income = higher rebates. This is never stored or shared.'
    }
  ];

  // Determine which question to show
  const currentQuestion = questions.find(q => !inputs[q.key as keyof CalculatorInputs] && !q.skip);
  const currentIndex = currentQuestion ? questions.indexOf(currentQuestion) : -1;
  const progress = Math.max(0, (step / questions.length) * 100);

  const handleAnswer = (value: any) => {
    setInputs(prev => ({
      ...prev,
      [currentQuestion!.key]: value
    }));
    setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1);
      const prevQuestion = questions[step - 1];
      setInputs(prev => {
        const updated = { ...prev };
        delete updated[prevQuestion.key as keyof CalculatorInputs];
        return updated;
      });
    }
  };

  const handleSubmit = () => {
    if (inputs.city && inputs.own_rent && inputs.home_type && inputs.heating_fuel && inputs.built_year && inputs.household_size && inputs.household_income) {
      const calcs = calculateRebates(inputs as CalculatorInputs);
      setResults(calcs);
      setShowResults(true);

      // Log to analytics
      console.log('Calculator completed', calcs);
    }
  };

  // Check if all required questions answered
  const allAnswered = questions.every(q => q.skip || inputs[q.key as keyof CalculatorInputs]);

  if (showResults && results) {
    return <CalculatorResults results={results} onReset={() => setShowResults(false)} />;
  }

  if (!currentQuestion) {
    // All questions answered, show submit
    return (
      <div className="max-w-lg mx-auto p-6 bg-white rounded-lg border border-gray-200">
        <h2 className="text-2xl font-bold mb-4">Ready to see your rebates?</h2>
        <p className="text-gray-600 mb-6">
          Based on your answers, we'll show you personalized rebates for {inputs.city}, {inputs.home_type} home, {inputs.heating_fuel} heating.
        </p>
        <div className="flex gap-3">
          <button
            onClick={handleBack}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Back
          </button>
          <button
            onClick={handleSubmit}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold"
          >
            See my rebates
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`w-full ${embedded ? 'max-w-md' : 'max-w-lg'} mx-auto p-6 bg-white rounded-lg border border-gray-200`}>
      {/* Progress */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Question {step + 1} of {questions.length}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Question */}
      <h2 className="text-xl font-bold mb-4">{currentQuestion.title}</h2>

      {currentQuestion.type === 'select' && (
        <select
          value={inputs[currentQuestion.key as keyof CalculatorInputs] || ''}
          onChange={(e) => handleAnswer(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Select a city...</option>
          {currentQuestion.options?.map((opt: any) => (
            <option key={opt.value || opt} value={opt.value || opt}>
              {opt.label || opt}
            </option>
          ))}
        </select>
      )}

      {currentQuestion.type === 'choice' && (
        <div className="space-y-3">
          {currentQuestion.options?.map((opt: any) => (
            <button
              key={opt.value}
              onClick={() => handleAnswer(opt.value)}
              className="w-full p-4 text-left border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-blue-500 transition"
            >
              {opt.label}
            </button>
          ))}
          {currentQuestion.hint && (
            <p className="text-xs text-gray-500 mt-4">{currentQuestion.hint}</p>
          )}
        </div>
      )}

      {currentQuestion.type === 'number' && (
        <div className="grid grid-cols-4 gap-2">
          {currentQuestion.options?.map((size: number) => (
            <button
              key={size}
              onClick={() => handleAnswer(size)}
              className="p-3 border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-blue-500 font-semibold text-center transition"
            >
              {size}
            </button>
          ))}
        </div>
      )}

      {/* Navigation */}
      <div className="flex gap-3 mt-8">
        {step > 0 && (
          <button
            onClick={handleBack}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Back
          </button>
        )}
        <button
          onClick={() => handleAnswer(inputs[currentQuestion.key as keyof CalculatorInputs])}
          disabled={!inputs[currentQuestion.key as keyof CalculatorInputs]}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
        >
          Next
        </button>
      </div>
    </div>
  );
}
