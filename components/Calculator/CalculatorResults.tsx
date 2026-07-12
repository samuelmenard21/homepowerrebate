'use client';

import { useState } from 'react';
import { CalculatorResults, encodeCalculatorUrl } from '@/lib/calculator/rebateCalculator';

interface CalculatorResultsProps {
  results: CalculatorResults;
  onReset: () => void;
}

export default function CalculatorResultsComponent({ results, onReset }: CalculatorResultsProps) {
  const [selectedUpgrades, setSelectedUpgrades] = useState<string[]>(
    results.upgrades.map(u => u.upgrade)
  );
  const [email, setEmail] = useState('');
  const [emailSubmitted, setEmailSubmitted] = useState(false);
  const [shareLink, setShareLink] = useState('');

  // Recalculate totals based on selected upgrades
  const visibleUpgrades = results.upgrades.filter(u => selectedUpgrades.includes(u.upgrade));
  const totalRebates = visibleUpgrades.reduce((sum, u) => sum + (u.rebate_amount || 0), 0);
  const monthlyBillImpact = visibleUpgrades.reduce((sum, u) => sum + (u.estimated_monthly_savings || 0), 0);

  const handleToggleUpgrade = (upgrade: string) => {
    setSelectedUpgrades(prev =>
      prev.includes(upgrade)
        ? prev.filter(u => u !== upgrade)
        : [...prev, upgrade]
    );
  };

  const handleEmailCapture = async (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Send to rebate alerts API
    console.log('Email captured:', email);
    setEmailSubmitted(true);
    setTimeout(() => setEmailSubmitted(false), 3000);
  };

  const handleShareLink = () => {
    const query = encodeCalculatorUrl({
      city: results.city,
      own_rent: results.is_renter ? 'rent' : 'own',
      home_type: results.home_type as any,
      heating_fuel: results.heating_fuel as any,
      built_year: undefined, // Don't encode for simplicity
      household_size: results.household_size,
      household_income: results.income_level as any,
      selected_upgrades: selectedUpgrades
    });
    const url = `${window.location.origin}/calculator?${query}`;
    setShareLink(url);
    navigator.clipboard.writeText(url);
  };

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white rounded-lg">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">
          Your rebate plan for {results.city}
        </h1>
        <p className="text-gray-600">
          {results.home_type} home, {results.heating_fuel} heating, {results.household_size} people
        </p>
      </div>

      {/* Total Summary */}
      <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 mb-8">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">Your realistic total</p>
            <p className="text-3xl font-bold text-blue-600">
              ${totalRebates.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Estimated net cost</p>
            <p className="text-2xl font-semibold">
              ${(results.estimated_net_cost_total - totalRebates).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Monthly bill impact</p>
            <p className="text-2xl font-semibold text-green-600">
              -${Math.abs(monthlyBillImpact).toLocaleString()}/mo
            </p>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-4">
          Best case across all upgrades in {results.city}: $
          {Math.max(...results.upgrades.map(u => u.rebate_amount_high || 0)).toLocaleString()}
        </p>
      </div>

      {/* Recommended Sequence Table */}
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-4">Recommended sequence (toggle to customize)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-gray-300">
                <th className="text-left py-3 px-3 font-semibold">#</th>
                <th className="text-left py-3 px-3 font-semibold">Upgrade</th>
                <th className="text-right py-3 px-3 font-semibold">Your rebate</th>
                <th className="text-right py-3 px-3 font-semibold">Net cost</th>
                <th className="text-left py-3 px-3 font-semibold">Why this order</th>
              </tr>
            </thead>
            <tbody>
              {results.upgrades.map((upgrade, idx) => (
                <tr
                  key={upgrade.upgrade}
                  className={`border-b ${selectedUpgrades.includes(upgrade.upgrade) ? 'bg-white' : 'bg-gray-50'}`}
                >
                  <td className="py-3 px-3">
                    <input
                      type="checkbox"
                      checked={selectedUpgrades.includes(upgrade.upgrade)}
                      onChange={() => handleToggleUpgrade(upgrade.upgrade)}
                      className="w-5 h-5 rounded cursor-pointer"
                    />
                  </td>
                  <td className="py-3 px-3">
                    <span className="font-semibold">{upgrade.label}</span>
                  </td>
                  <td className="text-right py-3 px-3 font-semibold">
                    ${upgrade.rebate_amount?.toLocaleString() || 0}
                  </td>
                  <td className="text-right py-3 px-3">
                    ${upgrade.typical_net_cost?.toLocaleString() || 'varies'}
                  </td>
                  <td className="py-3 px-3 text-gray-600 text-xs">
                    {upgrade.order === 1 && "Shrinks the heat pump you'll need"}
                    {upgrade.order === 2 && "Core heating upgrade, highest rebate"}
                    {upgrade.order === 3 && "Generates clean power"}
                    {upgrade.order === 4 && "Stores excess solar for peak hours"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Free Offerings */}
      {results.free_offerings.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
          <h3 className="font-semibold text-green-900 mb-3">Free offers you qualify for</h3>
          <ul className="space-y-2">
            {results.free_offerings.map((offer, idx) => (
              <li key={idx} className="text-sm text-green-900 flex items-start gap-2">
                <span className="text-lg">✓</span>
                <span>{offer}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* This Week Action List */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 mb-8">
        <h3 className="font-semibold text-amber-900 mb-3">This week, do this</h3>
        <ol className="space-y-2">
          {results.next_actions.map((action, idx) => (
            <li key={idx} className="text-sm text-amber-900 flex items-start gap-3">
              <span className="font-semibold min-w-6">{idx + 1}.</span>
              <span>{action}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* Share, Email, Installer Match */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {/* Share */}
        <div>
          <button
            onClick={handleShareLink}
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold text-sm"
          >
            📋 Copy link
          </button>
          <p className="text-xs text-gray-500 mt-2">Share with your spouse or partner</p>
        </div>

        {/* Email */}
        <form onSubmit={handleEmailCapture} className="flex flex-col">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="mt-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 font-semibold text-sm"
          >
            💌 Email me this
          </button>
          <p className="text-xs text-gray-500 mt-2">Plan + rebate alerts</p>
        </form>

        {/* Installer Match */}
        <div>
          {!results.is_renter && !results.is_condo && (
            <button className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold text-sm">
              🔗 Get matched
            </button>
          )}
          <p className="text-xs text-gray-500 mt-2">
            {results.is_renter || results.is_condo
              ? 'Not available for renters/condos yet'
              : 'Connect with vetted installers'}
          </p>
        </div>
      </div>

      {/* Back Button */}
      <button
        onClick={onReset}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 font-semibold"
      >
        ← Start over
      </button>
    </div>
  );
}
