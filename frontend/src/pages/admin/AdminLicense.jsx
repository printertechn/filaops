import React, { useState, useEffect } from "react";
import { useFeatureFlags } from "../../hooks/useFeatureFlags";

const AdminLicense = () => {
  const {
    tier,
    isPro,
    isEnterprise,
    loading: flagsLoading,
  } = useFeatureFlags();
  const [licenseKey, setLicenseKey] = useState("");
  const [activating, setActivating] = useState(false);
  const [licenseInfo, setLicenseInfo] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    fetchLicenseInfo();
  }, []);

  const fetchLicenseInfo = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        "http://127.0.0.1:8000/api/v1/license/info",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setLicenseInfo(data);
      }
    } catch (error) {
      // License info fetch failed - license section will be empty
    }
  };

  const handleActivate = async (e) => {
    e.preventDefault();
    setActivating(true);
    setError(null);
    setSuccess(null);

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        "http://127.0.0.1:8000/api/v1/license/activate",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ license_key: licenseKey }),
        }
      );

      const data = await response.json();

      if (response.ok) {
        setSuccess(
          `License activated! You now have ${data.tier.toUpperCase()} tier access.`
        );
        setLicenseKey("");
        // Refresh feature flags
        window.location.reload();
      } else {
        setError(data.detail || "Failed to activate license");
      }
    } catch (error) {
      setError("Failed to activate license. Please try again.");
    } finally {
      setActivating(false);
    }
  };

  const handleDeactivate = async () => {
    if (
      !confirm(
        "Are you sure you want to deactivate your license? You will lose access to Pro features."
      )
    ) {
      return;
    }

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        "http://127.0.0.1:8000/api/v1/license/deactivate",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        setSuccess("License deactivated. You are now on the Open tier.");
        window.location.reload();
      }
    } catch (error) {
      setError("Failed to deactivate license");
    }
  };

  if (flagsLoading) {
    return <div className="p-6 text-white">Loading...</div>;
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">
          License Management
        </h1>
        <p className="text-gray-400">
          Activate your Pro or Enterprise license to unlock advanced features
        </p>
      </div>

      {/* Current Status */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">
          Current License Status
        </h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Tier:</span>
            <span
              className={`font-bold ${
                tier === "pro"
                  ? "text-blue-400"
                  : tier === "enterprise"
                  ? "text-purple-400"
                  : "text-gray-400"
              }`}
            >
              {tier.toUpperCase()}
            </span>
          </div>
          {licenseInfo && (
            <>
              {licenseInfo.license_key && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">License Key:</span>
                  <span className="text-white font-mono">
                    {licenseInfo.license_key}
                  </span>
                </div>
              )}
              {licenseInfo.activated_at && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Activated:</span>
                  <span className="text-white">
                    {new Date(licenseInfo.activated_at).toLocaleDateString()}
                  </span>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Activation Form */}
      {!isPro && !isEnterprise && (
        <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">
            Activate License
          </h2>
          <p className="text-gray-300 mb-6">
            Enter your license key to unlock Pro or Enterprise features. License
            keys are provided when you purchase FilaOps Pro or Enterprise.
          </p>

          <form onSubmit={handleActivate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                License Key
              </label>
              <input
                type="text"
                value={licenseKey}
                onChange={(e) => setLicenseKey(e.target.value.toUpperCase())}
                placeholder="PRO-XXXX-XXXX-XXXX or ENT-XXXX-XXXX-XXXX"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
              <p className="mt-2 text-sm text-gray-400">
                For testing: Use{" "}
                <code className="bg-gray-700 px-2 py-1 rounded">
                  PRO-1234-5678-9012
                </code>{" "}
                or{" "}
                <code className="bg-gray-700 px-2 py-1 rounded">TEST-PRO</code>
              </p>
            </div>

            {error && (
              <div className="bg-red-900/50 border border-red-500/30 rounded-lg p-4">
                <p className="text-red-400">{error}</p>
              </div>
            )}

            {success && (
              <div className="bg-green-900/50 border border-green-500/30 rounded-lg p-4">
                <p className="text-green-400">{success}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={activating || !licenseKey}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              {activating ? "Activating..." : "Activate License"}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-3">
              Don't have a license?
            </h3>
            <p className="text-gray-300 mb-4">
              FilaOps Pro and Enterprise are coming in 2026. Join the waitlist
              to be notified when they're available!
            </p>
            <a
              href="https://github.com/Blb3D/filaops/discussions"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block bg-gray-700 hover:bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
            >
              Join Waitlist
            </a>
          </div>
        </div>
      )}

      {/* Active License Info */}
      {(isPro || isEnterprise) && (
        <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-semibold text-green-400 mb-2">
                ✓ {tier.toUpperCase()} License Active
              </h2>
              <p className="text-gray-300">
                You have access to all{" "}
                {tier === "enterprise" ? "Enterprise" : "Pro"} features.
              </p>
            </div>
            <button
              onClick={handleDeactivate}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              Deactivate
            </button>
          </div>
        </div>
      )}

      {/* Feature Comparison */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">
          Feature Comparison
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="pb-2 text-gray-400">Feature</th>
                <th className="pb-2 text-gray-400 text-center">Open</th>
                <th className="pb-2 text-blue-400 text-center">Pro</th>
                <th className="pb-2 text-purple-400 text-center">Enterprise</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              <tr className="border-b border-gray-700">
                <td className="py-2 text-white">Core ERP</td>
                <td className="py-2 text-green-400 text-center">✓</td>
                <td className="py-2 text-green-400 text-center">✓</td>
                <td className="py-2 text-green-400 text-center">✓</td>
              </tr>
              <tr className="border-b border-gray-700">
                <td className="py-2 text-white">Advanced Analytics</td>
                <td className="py-2 text-gray-500 text-center">-</td>
                <td className="py-2 text-green-400 text-center">✓</td>
                <td className="py-2 text-green-400 text-center">✓</td>
              </tr>
              <tr className="border-b border-gray-700">
                <td className="py-2 text-white">Customer Quote Portal</td>
                <td className="py-2 text-gray-500 text-center">-</td>
                <td className="py-2 text-green-400 text-center">✓</td>
                <td className="py-2 text-green-400 text-center">✓</td>
              </tr>
              <tr className="border-b border-gray-700">
                <td className="py-2 text-white">ML Time Estimation</td>
                <td className="py-2 text-gray-500 text-center">-</td>
                <td className="py-2 text-gray-500 text-center">-</td>
                <td className="py-2 text-green-400 text-center">✓</td>
              </tr>
              <tr>
                <td className="py-2 text-white">Printer Fleet Management</td>
                <td className="py-2 text-gray-500 text-center">-</td>
                <td className="py-2 text-gray-500 text-center">-</td>
                <td className="py-2 text-green-400 text-center">✓</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminLicense;
