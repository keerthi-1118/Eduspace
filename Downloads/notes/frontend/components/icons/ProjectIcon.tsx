import React from 'react';

const ProjectIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h12A2.25 2.25 0 0020.25 14.25V3M3.75 3v-1.5A2.25 2.25 0 016 0h12a2.25 2.25 0 012.25 2.25v1.5M3.75 3h16.5M16.5 6.75h.008v.008H16.5V6.75zM12 6.75h.008v.008H12V6.75zM7.5 6.75h.008v.008H7.5V6.75z" />
  </svg>
);

export default ProjectIcon;
