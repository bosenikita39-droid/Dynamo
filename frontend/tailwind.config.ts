import type { Config } from 'tailwindcss';
const config:Config={content:['./app/**/*.{ts,tsx}','./components/**/*.{ts,tsx}'],theme:{extend:{colors:{mission:{bg:'#080d19',panel:'#111a2a',cyan:'#56d5f5',violet:'#9478ff'}}}},plugins:[]};
export default config;
