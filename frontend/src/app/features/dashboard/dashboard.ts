import {Component} from '@angular/core';
import {CommonModule} from '@angular/common';
import {DomSanitizer, SafeResourceUrl} from '@angular/platform-browser';
import {environment} from '../../../environments/environment';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatButtonToggle, MatButtonToggleGroup} from '@angular/material/button-toggle';
import {FormsModule} from '@angular/forms';

@Component({
    selector: 'app-dashboard',
    imports: [CommonModule, MatExpansionModule, MatButtonToggleGroup, MatButtonToggle, FormsModule],
    templateUrl: './dashboard.html',
    styleUrl: './dashboard.css',
})
export class Dashboard {
    dashboards: { id: string; url: SafeResourceUrl }[];
    selectedDashboardId = 'PI1';

    constructor(private sanitizer: DomSanitizer) {
        this.dashboards = [
            {
                id: 'PI1',
                url: this.sanitizer.bypassSecurityTrustResourceUrl(environment.grafanaPi1DashboardUrl),
            },
            {
                id: 'PI2',
                url: this.sanitizer.bypassSecurityTrustResourceUrl("https://example.com/tmp1"),
            },
            {
                id: 'PI3',
                url: this.sanitizer.bypassSecurityTrustResourceUrl("https://example.com/tmp2"),
            },
        ];
    }
}
