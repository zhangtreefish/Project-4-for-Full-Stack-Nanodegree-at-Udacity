import Game from '../index';
import { shallow } from 'enzyme';
import { shallowToJson } from 'enzyme-to-json';
import React from 'react';

describe('<Game />', () => {
  it('should render with default props', () => {
    const wrapper = shallow(
      <Game />
    );
    expect(shallowToJson(wrapper)).toMatchSnapshot();
  });
});
