import * as React from 'react';
import {cn} from '@/lib/cn';
/** shadcn/ui-style display primitive. */
export function Badge({children,className,...props}:React.HTMLAttributes<HTMLSpanElement>){return <span className={cn('demo-label',className)} {...props}>{children}</span>}
