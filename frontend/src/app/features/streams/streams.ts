import {Component} from '@angular/core';
import {environment} from '../../../environments/environment';

@Component({
    selector: 'app-streams',
    imports: [],
    templateUrl: './streams.html',
    styleUrl: './streams.css',
})
export class Streams {
    streamErrors: Record<string, boolean> = {};

    streams = [
        {
            id: 'front-entrance',
            label: 'Front Entrance',
            url: environment.frontEntranceCameraStreamUrl,
        },
    ];

    setStreamError(id: string) {
        this.streamErrors[id] = true;
    }
}
