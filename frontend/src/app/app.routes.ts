import {Routes} from '@angular/router';
import {Dashboard} from './features/dashboard/dashboard';
import {Security} from './features/security/security';
import {Sensors} from './features/sensors/sensors';
import {Stats} from './features/stats/stats';
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
        path: 'sensors',
        component: Sensors,
    },
    {
        path: 'stats',
        component: Stats,
    },
    {path: '', redirectTo: 'dashboard', pathMatch: 'full'},
    {path: '**', redirectTo: 'dashboard', pathMatch: 'full'},
];
