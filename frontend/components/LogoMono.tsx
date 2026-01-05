export default function LogoMono({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 520 150"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <style>
          {`.cls-light { fill: #ffffff; }
          .cls-gold { fill: #d4af37; }
          .cls-font-bold { font-family: sans-serif; font-weight: bold; }
          .cls-font-reg { font-family: sans-serif; font-weight: normal; letter-spacing: 1px;}`}
        </style>
      </defs>
      <g id="Icon-Mono">
        <path className="cls-light" d="M75,10A65,65,0,1,0,140,75,65.07,65.07,0,0,0,75,10Zm0,120a55,55,0,1,1,55-55A55.06,55.06,0,0,1,75,130Z"/>
        <rect className="cls-light" x="35" y="65" width="80" height="5"/>
        <rect className="cls-light" x="45" y="85" width="60" height="5"/>
        <path className="cls-light" d="M75,30,60,60H90Z"/>
        <rect className="cls-light" x="70" y="60" width="10" height="35"/>
        <path className="cls-gold" d="M75,120l15-25H60Z"/>
      </g>
      <g id="Text-Mono">
        <rect className="cls-gold" x="160" y="30" width="60" height="3"/>
        <text className="cls-light cls-font-bold" transform="translate(160 50)" fontSize="20">JUNIOR MINING</text>
        <text className="cls-gold cls-font-reg" transform="translate(160 80)" fontSize="36">INTELLIGENCE</text>
      </g>
    </svg>
  );
}
