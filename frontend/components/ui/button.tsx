'use client';
import * as React from 'react';
import {Slot} from '@radix-ui/react-slot';
import {cn} from '@/lib/cn';
/** shadcn/ui-style locally owned button primitive; no backend behavior. */
type Props=React.ButtonHTMLAttributes<HTMLButtonElement>&{asChild?:boolean;variant?:'primary'|'outline'|'ghost'};
export const Button=React.forwardRef<HTMLButtonElement,Props>(({asChild=false,variant='primary',className,...props},ref)=>{
 const Component=asChild?Slot:'button';
 return <Component ref={ref} className={cn(variant==='primary'?'primary-button':variant==='outline'?'outline-button':'ghost-button',className)} {...props}/>;
});
Button.displayName='Button';
