import type {Metadata} from 'next';
import './globals.css';
import './mission-v3.css';
import './login-v3.css';
export const metadata:Metadata={title:'SignalTrust | Mission Health Intelligence',description:'Research prototype: astronaut-health and physiological signal-reliability mission control'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
