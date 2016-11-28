import React, { PropTypes } from 'react';

import styles from './index.module.scss';
import cssModules from 'react-css-modules';

const Game = (props) => (
  <div className={styles.game}>
  </div>
);

Game.propTypes = {

};

export default cssModules(Game, styles);
