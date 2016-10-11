import {
  LOAD_DATA_INITIATION,
  LOAD_DATA_SUCCESS,
  LOAD_DATA_FAILURE,
  CLEAR_DATA_ERROR,
} from './constants';
import 'whatwg-fetch';
const baseUrl = 'https://tictactoe-2016.appspot.com/_ah/';
const gamesUrl = `${baseUrl}api/tictactoe/v1/all_games`;

// loadDataInitiation :: None -> {Action}
export const loadDataInitiation = () => ({
  type: LOAD_DATA_INITIATION,
});

// loadDataSuccess :: JSON -> {Action}
export const loadDataSuccess = (games) => ({
  type: LOAD_DATA_SUCCESS,
  games,
});

// loadDataFailure :: JSON -> {Action}
export const loadDataFailure = (errors) => ({
  type: LOAD_DATA_FAILURE,
  errors,
});

// clearDataError :: None -> {Action}
export const clearDataError = () => ({
  type: CLEAR_DATA_ERROR,
});

// loadAllGames :: None -> Thunk
export const loadGames = () =>
  (dispatch) => {
    dispatch(
      loadDataInitiation()
    );
    fetch(gamesUrl)
      .then(res => {
        console.log(`data?{res.json()}`);
        return res.json();
      })
      .then(res => res.items)
      .then(games =>
        games.filter(game => !game.gameOver)
      )
      .then(games =>
        games.sort((a, b) =>
          a.seatsAvailable - b.seatsAvailable
        )
      )
      .then(games => games.slice(0, 4))
      .then(games => {
        dispatch(
          loadDataSuccess(games)
        );
      }).catch(error =>
        dispatch(
          loadDataFailure([error])
        )
      );
  };
