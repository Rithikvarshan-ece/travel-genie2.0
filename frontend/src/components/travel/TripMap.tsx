import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const INR = (v: number | string | undefined | null): string => {
  const n = typeof v === 'string' ? parseFloat(v) : (v ?? NaN);
  if (!isFinite(n)) return '₹N/A';
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n * 83);
};

const costToINR = (cost: string | undefined): string => {
  if (!cost) return 'Free';
  const num = parseFloat(cost.replace(/[^0-9.]/g, ''));
  if (!isFinite(num) || num === 0) return 'Free';
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(num * 83);
};

const makeIcon = (color: string, emoji: string) =>
  L.divIcon({
    className: '',
    html: `<div style="background:${color};width:32px;height:32px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;">
             <span style="transform:rotate(45deg);font-size:14px">${emoji}</span>
           </div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -34],
  });

const destIcon  = makeIcon('#6366f1', '📍');
const hotelIcon = makeIcon('#10b981', '🏨');
const attrIcon  = makeIcon('#f59e0b', '⭐');

function FitBounds({ positions }: { positions: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (positions.length > 0) {
      map.fitBounds(L.latLngBounds(positions), { padding: [40, 40] });
    }
  }, [map, positions]);
  return null;
}

interface Props {
  destination?: { name?: string; latitude?: number; longitude?: number };
  hotels?: { name: string; latitude?: number; longitude?: number; price_per_night?: number; rating?: number }[];
  attractions?: { name: string; type?: string; cost?: string }[];
  destLat?: number;
  destLng?: number;
}

export default function TripMap({ destination, hotels = [], attractions = [], destLat, destLng }: Props) {
  const lat = destLat ?? destination?.latitude;
  const lng = destLng ?? destination?.longitude;

  if (!lat || !lng) {
    return (
      <div className="h-64 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400 text-sm">
        Map unavailable — no coordinates
      </div>
    );
  }

  const center: [number, number] = [lat, lng];
  const hotelMarkers = hotels.filter(h => h.latitude && h.longitude);
  const allPositions: [number, number][] = [
    center,
    ...hotelMarkers.map(h => [h.latitude!, h.longitude!] as [number, number]),
  ];

  return (
    <MapContainer center={center} zoom={12} style={{ height: '360px', borderRadius: '1rem' }} scrollWheelZoom={false}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds positions={allPositions} />

      {/* Destination pin */}
      <Marker position={center} icon={destIcon}>
        <Popup><strong>{destination?.name ?? 'Destination'}</strong></Popup>
      </Marker>

      {/* Hotel pins */}
      {hotelMarkers.map((h, i) => (
        <Marker key={i} position={[h.latitude!, h.longitude!]} icon={hotelIcon}>
          <Popup>
            <strong>{h.name}</strong><br />
            {INR(h.price_per_night)}/night · ⭐ {h.rating ?? '—'}
          </Popup>
        </Marker>
      ))}

      {/* Attraction pins — offset slightly so they don't stack on destination */}
      {attractions.slice(0, 5).map((a, i) => (
        <Marker
          key={i}
          position={[lat + (i + 1) * 0.003, lng + (i % 2 === 0 ? 0.004 : -0.004)]}
          icon={attrIcon}
        >
          <Popup><strong>{a.name}</strong><br />{a.type} · {costToINR(a.cost)}</Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
