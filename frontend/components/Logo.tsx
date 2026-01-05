export default function Logo({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 500 150"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Circular Icon Background */}
      <circle cx="75" cy="75" r="60" fill="#212f3c" stroke="#d4af37" strokeWidth="3"/>

      {/* Mining Shaft Symbol - Up Arrow */}
      <path d="M75 35 L85 45 L80 45 L80 55 L70 55 L70 45 L65 45 Z" fill="#d4af37"/>

      {/* Horizontal Bars (Mining Levels) */}
      <rect x="50" y="65" width="50" height="3" fill="#d4af37"/>
      <rect x="50" y="75" width="50" height="3" fill="#d4af37"/>
      <rect x="50" y="85" width="50" height="3" fill="#d4af37"/>

      {/* Mining Shaft Symbol - Down Arrow */}
      <path d="M75 115 L65 105 L70 105 L70 95 L80 95 L80 105 L85 105 Z" fill="#d4af37"/>

      {/* Company Name */}
      <text x="160" y="65" fontFamily="Arial, sans-serif" fontSize="36" fontWeight="bold" fill="#212f3c">
        MINING
      </text>
      <text x="300" y="65" fontFamily="Arial, sans-serif" fontSize="36" fontWeight="300" fill="#555">
        INTEL
      </text>

      {/* Tagline */}
      <text x="160" y="95" fontFamily="Arial, sans-serif" fontSize="14" fontWeight="300" fill="#888" letterSpacing="2">
        JUNIOR MINING INTELLIGENCE
      </text>

      {/* Decorative underline */}
      <line x1="160" y1="105" x2="480" y2="105" stroke="#d4af37" strokeWidth="2"/>
    </svg>
  );
}
