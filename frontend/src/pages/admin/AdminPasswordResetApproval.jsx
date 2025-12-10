import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { API_URL } from "../../config/api";

export default function AdminPasswordResetApproval() {
  const { action, token } = useParams();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    processApproval();
  }, [action, token]);

  const processApproval = async () => {
    try {
      const endpoint = action === "approve"
        ? `${API_URL}/api/v1/auth/password-reset/approve/${token}`
        : `${API_URL}/api/v1/auth/password-reset/deny/${token}`;

      const res = await fetch(endpoint);

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to process request");
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Processing request...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
        <div className="w-full max-w-md text-center">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-8">
            <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">Error</h1>
            <p className="text-gray-400 mb-6">{error}</p>
            <Link
              to="/admin"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Go to Admin Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const isApproved = action === "approve";

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-md text-center">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8">
          <div className={`w-16 h-16 ${isApproved ? 'bg-green-500/20' : 'bg-red-500/20'} rounded-full flex items-center justify-center mx-auto mb-6`}>
            {isApproved ? (
              <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
          </div>

          <h1 className="text-2xl font-bold text-white mb-4">
            Password Reset {isApproved ? "Approved" : "Denied"}
          </h1>

          <div className="bg-gray-800 rounded-lg p-4 mb-6 text-left">
            <div className="text-sm">
              <p className="text-gray-400">User Email:</p>
              <p className="text-white font-medium">{result?.user_email}</p>
            </div>
            <div className="text-sm mt-3">
              <p className="text-gray-400">Status:</p>
              <p className={`font-medium ${isApproved ? 'text-green-400' : 'text-red-400'}`}>
                {result?.status?.toUpperCase()}
              </p>
            </div>
          </div>

          <p className="text-gray-400 mb-6">
            {isApproved
              ? "The user has been notified and can now reset their password."
              : "The user has been notified that their request was denied."}
          </p>

          <Link
            to="/admin"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Go to Admin Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
