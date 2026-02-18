import {ComponentFixture, TestBed} from '@angular/core/testing';

import {Readings} from './readings';

describe('Readings', () => {
    let component: Readings;
    let fixture: ComponentFixture<Readings>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [Readings]
        })
            .compileComponents();

        fixture = TestBed.createComponent(Readings);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
