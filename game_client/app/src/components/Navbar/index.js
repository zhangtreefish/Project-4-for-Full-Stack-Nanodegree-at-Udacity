import React from 'react';
import Header from 'grommet-udacity/components/Header';
import Title from 'grommet-udacity/components/Title';
import Menu from 'grommet-udacity/components/Menu';
import Anchor from 'grommet-udacity/components/Anchor';
import Search from 'grommet-udacity/components/Search';

import styles from './index.module.scss';
import cssModules from 'react-css-modules';

const Navbar = () => (
  <div className={styles.navbar}>
    <Header justify="between">
      <Title>
        <img className={styles.logo} src="https://d30y9cdsu7xlg0.cloudfront.net/png/76612-200.png" alt="logo" />
      </Title>
      <Menu direction="row" align="center" responsive={false}>
        <Anchor href="#" className="active">
          Games
        </Anchor>
        <Anchor href="#">
          Players
        </Anchor>
        <Search dropAlign={{ right: 'right' }} />
      </Menu>
    </Header>
  </div>
);

export default cssModules(Navbar, styles);
