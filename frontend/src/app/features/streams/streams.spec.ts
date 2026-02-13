import {ComponentFixture, TestBed} from '@angular/core/testing';

import {Streams} from './streams';

describe('Streams', () => {
    let component: Streams;
    let fixture: ComponentFixture<Streams>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [Streams]
        })
            .compileComponents();

        fixture = TestBed.createComponent(Streams);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
