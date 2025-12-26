import React from 'react';

const PreviewIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 20.25h12m-7.5-3v3m3-3v3m-10.125-3.875H3V4.5A2.25 2.25 0 015.25 2.25h13.5A2.25 2.25 0 0121 4.5v12a2.25 2.25 0 01-2.25 2.25H13.875" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 8.25L15 12l-4.5 3.75" />
  </svg>
);

export default PreviewIcon;
