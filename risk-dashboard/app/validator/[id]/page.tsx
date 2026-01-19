"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { Shield, ShieldAlert, Activity, ArrowLeft, TrendingUp, Zap, Server, Lock } from 'lucide-react';

export default function ValidatorDetails() {
    const params = useParams();
    const id = params.id as string;

    const [data, setData] = useState<any>(null);
    const [history, setHistory] = useState<number[]>([]);

    useEffect(() => {
        // Fetch base data
        const fetchData = async () => {
            try {
                // Try to get real agent data
                const res = await fetch('/risk_status.json');
                if (res.ok) {
                    const json = await res.json();
                    if (json.validator === id) {
                        setData(json);
                    } else {
                        // Fallback: Simulate data for this ID if it doesn't match agent's current target
                        setData({
                            validator: id,
                            score: Math.floor(Math.random() * 100),
                            details: {
                                concentration: Math.random(),
                                volatility: Math.random() * 0.2,
                                unstake_spike: Math.random() * 0.1
                            }
                        });
                    }
                }
            } catch (e) {
                console.error(e);
            }
        };

        fetchData();

        // Generate Mock History (30 Days)
        const mockHistory = Array.from({ length: 30 }, () => 8 + Math.random() * 4); // APY between 8% and 12%
        setHistory(mockHistory);

    }, [id]);

    if (!data) return <div className="p-24 text-slate-500 font-mono animate-pulse">ANALYZING CHAIN DATA...</div>;

    const riskScore = data.score;
    const isRisky = riskScore >= 50;

    return (
        <main className="flex min-h-screen flex-col items-center p-12 bg-black font-sans text-slate-200">
            <div className="w-full max-w-4xl">

                {/* NAV */}
                <Link href="/" className="flex items-center gap-2 text-emerald-500 hover:text-emerald-400 mb-8 font-bold uppercase tracking-widest text-xs transition-colors">
                    <ArrowLeft className="w-4 h-4" /> Back to Terminal
                </Link>

                {/* HERO HEADER */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 mb-8 backdrop-blur-sm relative overflow-hidden">
                    <div className={`absolute top-0 right-0 w-64 h-64 rounded-full blur-[100px] opacity-20 ${isRisky ? 'bg-red-600' : 'bg-emerald-600'}`}></div>

                    <div className="relative z-10 flex justify-between items-start">
                        <div>
                            <h1 className="text-sm text-slate-400 uppercase font-bold mb-2">Validator Identity</h1>
                            <div className="font-mono text-2xl text-white break-all max-w-xl">{id}</div>
                            <div className="flex gap-4 mt-6">
                                <Badge icon={<Activity className="w-3 h-3" />} label="Active" color="text-blue-400 bg-blue-900/30 border-blue-800" />
                                <Badge icon={<Lock className="w-3 h-3" />} label="KYC Verfiied" color="text-yellow-400 bg-yellow-900/30 border-yellow-800" />
                            </div>
                        </div>

                        <div className="text-right">
                            <div className="text-xs text-slate-500 uppercase font-bold mb-1">Current Risk Score</div>
                            <div className={`text-6xl font-black tracking-tighter ${isRisky ? 'text-red-500' : 'text-emerald-500'}`}>
                                {riskScore}
                            </div>
                        </div>
                    </div>
                </div>

                {/* GRID LAYOUT */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

                    {/* LEFT: METRICS */}
                    <div className="space-y-4">
                        <MetricCard
                            label="Stake Concentration"
                            value={(data.details.concentration * 100).toFixed(2) + "%"}
                            desc="Percentage of network stake held."
                            subValue={data.details.concentration > 0.33 ? "CRITICAL" : "HEALTHY"}
                            subColor={data.details.concentration > 0.33 ? "text-red-500" : "text-emerald-500"}
                            icon={<Server className="w-5 h-5 text-slate-400" />}
                        />
                        <MetricCard
                            label="Reward Volatility"
                            value={(data.details.volatility * 100).toFixed(2) + "%"}
                            desc="Variance in reward payouts (10 Era Avg)."
                            subValue="STABLE"
                            subColor="text-blue-500"
                            icon={<TrendingUp className="w-5 h-5 text-slate-400" />}
                        />
                        <MetricCard
                            label="Slashing Events"
                            value="0"
                            desc="Validators slashed in last 90 days."
                            subValue="PERFECT RECORD"
                            subColor="text-emerald-500"
                            icon={<Zap className="w-5 h-5 text-slate-400" />}
                        />
                    </div>

                    {/* RIGHT: CHART & AI */}
                    <div className="space-y-4">
                        {/* MOCK CHART */}
                        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 h-64 flex flex-col justify-between">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-slate-400 text-xs font-bold uppercase">30-Day APY Performance</h3>
                                <span className="text-emerald-500 text-xs font-bold">+10.4% Avg</span>
                            </div>

                            {/* Simple CSS Bar Chart */}
                            <div className="flex items-end justify-between h-32 gap-1">
                                {history.map((val, i) => (
                                    <div
                                        key={i}
                                        className="w-full bg-emerald-500/20 hover:bg-emerald-500/50 transition-colors rounded-sm relative group"
                                        style={{ height: `${(val / 15) * 100}%` }}
                                    >
                                        <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-[10px] p-1 rounded">
                                            {val.toFixed(1)}%
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="flex justify-between text-[10px] text-slate-600 font-mono mt-2">
                                <span>30 Days Ago</span>
                                <span>Today</span>
                            </div>
                        </div>

                        {/* AI ANALYSIS PLACEHOLDER */}
                        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
                            <div className="flex items-center gap-2 mb-4">
                                <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                                <h3 className="text-purple-400 text-xs font-bold uppercase">AI Risk Analysis</h3>
                            </div>
                            <p className="text-sm text-slate-400 leading-relaxed">
                                Analysis indicates that <span className="text-white font-mono">{id.substring(0, 10)}...</span> maintains a stable performance profile.
                                However, concentration metrics suggest they are approaching the <span className="text-yellow-500">upper quartile of influence</span>.
                                Volatility is negligible, making this a <span className="text-white font-bold">safe candidate</span> for diversified staking portfolios.
                            </p>
                        </div>

                    </div>
                </div>

            </div>
        </main>
    );
}

function MetricCard({ label, value, desc, subValue, subColor, icon }: any) {
    return (
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 hover:border-slate-600 transition-colors">
            <div className="flex justify-between items-start mb-2">
                <span className="text-slate-500 text-xs font-bold uppercase">{label}</span>
                {icon}
            </div>
            <div className="text-2xl font-mono text-white mb-1">{value}</div>
            <div className={`text-[10px] font-bold uppercase mb-2 ${subColor}`}>{subValue}</div>
            <div className="text-slate-600 text-xs leading-tight">{desc}</div>
        </div>
    );
}

function Badge({ icon, label, color }: any) {
    return (
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${color} text-xs font-bold uppercase`}>
            {icon}
            <span>{label}</span>
        </div>
    );
}
