import {Routes} from '@angular/router';
import {Dashboard} from './features/dashboard/dashboard';
import {Security} from './features/security/security';
import {Readings} from './features/readings/readings';
import {Lights} from './features/lights/lights';
import {Streams} from './features/streams/streams';
import {Timers} from './features/timers/timers';

export const routes: Routes = [
    {
        path: 'dashboard',
        component: Dashboard,
    },
    {
        path: 'streams',
        component: Streams,
    },
    {
        path: 'security',
        component: Security,
    },
    {
        path: 'timers',
        component: Timers,
    },
    {
        path: 'readings',
        component: Readings,
    },
    {
        path: 'lights',
        component: Lights,
    },
    {path: '', redirectTo: 'dashboard', pathMatch: 'full'},
    {path: '**', redirectTo: 'dashboard', pathMatch: 'full'},
];
