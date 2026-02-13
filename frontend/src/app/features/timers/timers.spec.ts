import {ComponentFixture, TestBed} from '@angular/core/testing';

import {Timers} from './timers';

describe('Timers', () => {
    let component: Timers;
    let fixture: ComponentFixture<Timers>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [Timers]
        })
            .compileComponents();

        fixture = TestBed.createComponent(Timers);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
