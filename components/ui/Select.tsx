import React from 'react';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  children: React.ReactNode;
}

export function Select({ children, className = '', ...props }: SelectProps) {
  return (
    <select
      className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm py-2 px-3 ${className}`}
      {...props}
    >
      {children}
    </select>
  );
}







