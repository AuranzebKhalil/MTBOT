"use client";
import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../components/AuthContext";
import { supabase } from "../lib/supabase";
import toast from "react-hot-toast";
import { useMediaQuery } from "../lib/useMediaQuery";
import { 
  User, Mail, Phone, Calendar, Globe, MapPin, 
  Briefcase, TrendingUp, Shield, Bell, Camera, 
  Save, Loader2, ChevronRight, Hash, Clock, Activity
} from "lucide-react";
import Image from "next/image";

export default function ProfilePage() {
  const { user, token } = useAuth();
  const isMobile = useMediaQuery("(max-width: 768px)");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState({
    full_name: "",
    username: "",
    email: "",
    phone: "",
    date_of_birth: "",
    country: "",
    city: "",
    address: "",
    trading_experience: "Beginner",
    preferred_symbols: [],
    account_currency: "USD",
    broker_name: "",
    risk_profile: "Moderate",
    timezone: "UTC",
    bio: "",
    avatar_url: "",
    notifications_enabled: true
  });

  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    const initSessionData = async () => {
      if (token) {
        await supabase.auth.setSession({
          access_token: token,
          refresh_token: localStorage.getItem("quant_refresh") || ""
        });
      }
      if (user) {
        fetchProfile();
      }
    };
    initSessionData();
  }, [user, token]);

  const fetchProfile = async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", user.id)
        .single();

      if (error && error.code !== "PGRST116") throw error;

      if (data) {
        setProfile((prev) => ({ ...prev, ...data }));
        if (data.avatar_url) getAvatarUrl(data.avatar_url);
      } else {
        setProfile((prev) => ({ ...prev, email: user.email || "" }));
      }
    } catch (err) {
      console.error("Fetch Error:", err);
      toast.error("Protocol Error: Identity Sync Failed");
      setProfile((prev) => ({ ...prev, email: user?.email || "" }));
    } finally {
      setLoading(false);
    }
  };

  const getAvatarUrl = async (path) => {
    const { data } = supabase.storage.from("profile-images").getPublicUrl(path);
    setPreviewUrl(data.publicUrl);
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setProfile((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) return toast.error("Image too large (Max 2MB)");
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleSave = async (e) => {
    if (e) e.preventDefault();
    try {
      setSaving(true);
      let avatarPath = profile.avatar_url;
      const file = fileInputRef.current?.files[0];
      if (file) {
        const fileExt = file.name.split(".").pop();
        avatarPath = `${user.id}/avatar.${fileExt}`;
        await supabase.storage.from("profile-images").upload(avatarPath, file, { upsert: true });
      }

      const { error } = await supabase.from("profiles").upsert({ ...profile, id: user.id, avatar_url: avatarPath, updated_at: new Date().toISOString() });
      if (error) throw error;
      toast.success("Identity Protocols Updated");
    } catch (err) {
      console.error("Save Error:", err);
      toast.error("Critical Save Fault");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}><Loader2 className="animate-spin" size={48} color="var(--primary)" /></div>;

  return (
    <div className="profile-container" style={{ paddingBottom: '40px' }}>
      <header style={{ marginBottom: isMobile ? '20px' : '32px' }}>
        <h1 style={{ fontSize: isMobile ? '22px' : '28px', fontWeight: '900', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '12px' }}>
           <User size={isMobile ? 24 : 32} color="var(--primary)" /> IDENTITY ENGINE
        </h1>
      </header>

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: isMobile ? '16px' : '24px' }}>
        <div className="glass-panel" style={{ padding: isMobile ? '16px' : '32px', borderRadius: '24px', border: '1px solid var(--border)', background: 'var(--bg-card)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? '20px' : '32px', flexWrap: 'wrap', justifyContent: isMobile ? 'center' : 'flex-start' }}>
            <div style={{ position: 'relative' }}>
              <div style={{ width: isMobile ? '100px' : '120px', height: isMobile ? '100px' : '120px', borderRadius: '50%', background: 'var(--gradient-auralith)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', border: '4px solid var(--border)' }}>
                {previewUrl ? <img src={previewUrl} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : <User size={isMobile ? 48 : 64} color="rgba(255,255,255,0.2)" />}
              </div>
              <button type="button" onClick={() => fileInputRef.current?.click()} style={{ position: 'absolute', bottom: '0', right: '0', background: 'var(--primary)', color: '#000', width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '3px solid var(--bg-card)', cursor: 'pointer' }}><Camera size={14} /></button>
              <input type="file" ref={fileInputRef} onChange={handleImageChange} accept="image/*" style={{ display: 'none' }} />
            </div>
            <div style={{ flex: 1, minWidth: isMobile ? '100%' : '300px', display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '12px' }}>
               <ProfileInput label="Full Name" name="full_name" value={profile.full_name} onChange={handleInputChange} icon={<User size={14} />} isMobile={isMobile} />
               <ProfileInput label="Alias" name="username" value={profile.username} onChange={handleInputChange} icon={<Hash size={14} />} isMobile={isMobile} />
               <ProfileInput label="Email" name="email" value={profile.email} readOnly icon={<Mail size={14} />} isMobile={isMobile} />
               <ProfileInput label="Phone" name="phone" value={profile.phone} onChange={handleInputChange} icon={<Phone size={14} />} isMobile={isMobile} />
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: isMobile ? '16px' : '24px' }}>
          <Panel title="Geographic Protocols" icon={<Globe size={16} />} isMobile={isMobile} color="var(--primary)">
            <div style={{ display: 'grid', gap: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <ProfileInput label="Country" name="country" value={profile.country} onChange={handleInputChange} icon={<Globe size={14} />} isMobile={isMobile} />
                <ProfileInput label="City" name="city" value={profile.city} onChange={handleInputChange} icon={<MapPin size={14} />} isMobile={isMobile} />
              </div>
              <ProfileInput label="Address" name="address" value={profile.address} onChange={handleInputChange} icon={<MapPin size={14} />} isMobile={isMobile} />
              <ProfileSelect label="Timezone" name="timezone" value={profile.timezone} onChange={handleInputChange} icon={<Clock size={14} />} options={["UTC", "GMT", "EST", "EDT", "BST"]} isMobile={isMobile} />
            </div>
          </Panel>

          <Panel title="Institutional Configs" icon={<Briefcase size={16} />} isMobile={isMobile} color="var(--accent)">
            <div style={{ display: 'grid', gap: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                 <ProfileSelect label="Experience" name="trading_experience" value={profile.trading_experience} onChange={handleInputChange} icon={<Activity size={14} />} options={["Beginner", "Advanced", "Institutional"]} isMobile={isMobile} />
                 <ProfileSelect label="Risk" name="risk_profile" value={profile.risk_profile} onChange={handleInputChange} icon={<Shield size={14} />} options={["Moderate", "Aggressive"]} isMobile={isMobile} />
              </div>
              <ProfileInput label="Broker" name="broker_name" value={profile.broker_name} onChange={handleInputChange} icon={<Globe size={14} />} isMobile={isMobile} />
              <ProfileSelect label="Currency" name="account_currency" value={profile.account_currency} onChange={handleInputChange} icon={<TrendingUp size={14} />} options={["USD", "EUR", "GBP"]} isMobile={isMobile} />
            </div>
          </Panel>
        </div>

        <Panel title="Intelligence & Preferences" icon={<Bell size={16} />} isMobile={isMobile} color="var(--text-main)">
           <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '10px', fontWeight: '800', color: 'var(--text-sub)', textTransform: 'uppercase' }}>Bio</label>
                <textarea name="bio" value={profile.bio} onChange={handleInputChange} style={{ width: '100%', minHeight: '80px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', borderRadius: '12px', padding: '12px', color: 'var(--text-main)', fontSize: '13px', resize: 'none' }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}><Bell size={16} color="var(--primary)" /><div style={{ fontSize: '13px', fontWeight: '800', color: 'var(--text-main)' }}>Notifications</div></div>
                <input type="checkbox" name="notifications_enabled" checked={profile.notifications_enabled} onChange={handleInputChange} style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--primary)' }} />
              </div>
           </div>
        </Panel>

        <button type="submit" disabled={saving} style={{ width: isMobile ? '100%' : 'auto', alignSelf: 'flex-end', background: 'var(--gradient-auralith)', color: '#000', padding: isMobile ? '14px' : '16px 48px', borderRadius: '14px', fontSize: '14px', fontWeight: '900', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
          {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />} {saving ? "SYNCING..." : "SAVE CONFIGURATION"}
        </button>
      </form>
    </div>
  );
}

function Panel({ title, icon, children, isMobile, color }) {
  return (
    <div className="glass-panel" style={{ padding: isMobile ? '16px' : '24px', borderRadius: '24px', border: '1px solid var(--border)', background: 'var(--bg-card)' }}>
      <h3 style={{ fontSize: '12px', fontWeight: '800', color: color, marginBottom: '16px', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '8px' }}>{icon} {title}</h3>
      {children}
    </div>
  );
}

function ProfileInput({ label, name, value, onChange, icon, type = "text", readOnly = false, isMobile }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      <label style={{ fontSize: '10px', fontWeight: '800', color: 'var(--text-sub)', textTransform: 'uppercase' }}>{label}</label>
      <div style={{ position: 'relative' }}>
        <div style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-sub)' }}>{icon}</div>
        <input type={type} name={name} value={value || ""} onChange={onChange} readOnly={readOnly} style={{ width: '100%', height: isMobile ? '40px' : '44px', padding: '0 12px 0 36px', background: readOnly ? 'transparent' : 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', borderRadius: '10px', color: readOnly ? 'var(--text-sub)' : 'var(--text-main)', fontSize: '13px', outline: 'none' }} />
      </div>
    </div>
  );
}

function ProfileSelect({ label, name, value, onChange, icon, options, isMobile }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      <label style={{ fontSize: '10px', fontWeight: '800', color: 'var(--text-sub)', textTransform: 'uppercase' }}>{label}</label>
      <div style={{ position: 'relative' }}>
        <div style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-sub)' }}>{icon}</div>
        <select name={name} value={value} onChange={onChange} style={{ width: '100%', height: isMobile ? '40px' : '44px', padding: '0 12px 0 36px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', borderRadius: '10px', color: 'var(--text-main)', fontSize: '13px', outline: 'none', appearance: 'none' }}>
          {options.map(opt => <option key={opt} value={opt} style={{ background: '#0a0e14' }}>{opt}</option>)}
        </select>
        <div style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: 'var(--text-sub)' }}>
           <ChevronRight size={12} style={{ transform: 'rotate(90deg)' }} />
        </div>
      </div>
    </div>
  );
}
